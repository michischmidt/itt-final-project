#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
# Script was written by Erik Blank and Michael Schmidt

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow
import pyqtgraph as pg
from pyqtgraph.flowchart import Flowchart, Node
import numpy as np
from DIPPID_pyqtnode import DIPPIDNode, BufferNode
import pyqtgraph.flowchart.library as fclib
import pandas as pd
import os
from sklearn import svm
from numpy import fromstring
import time
import fluidsynth
from ConvolutionNode import ConvolveNode

'''
Custom SVM node which can be switched between
inactive, traning and prediction.

Inactive: Do nothing

Traning mode: Continually read in sample data (in our case
a list of frequency components) and trains a SVM classifier
with the data (and previous data) (Note, he category for this sample
can be defined by a text field in the control pane)

Prediction: SVM node reads sample in and outputs the predicted category
as string.
'''
# Filename where our gestures are saved
TRAINING_DATA_FILE = "training_data.csv"

# The amount of transformed signals from the dippid we use for 1 gesture;
# the transfomation cuts the dippid signal amount in half
# to calculate to time per gesture do:
# DATA_LENGTH / (DippidFrequency * 2)
DATA_LENGTH = 30
TIME_FOR_DATA = 30000


class Drumkit(QMainWindow):
    def __init__(self):
        super(Drumkit, self).__init__()
        self.__init_ui()
        self.init_logger(TRAINING_DATA_FILE)
        self.init_nodes()
        self.is_predicting = False
        self.prediction_timer = QtCore.QTimer()
        self.prediction_timer.timeout.connect(self.update_prediction)
        self.is_training = False
        self.training_timer = QtCore.QTimer()
        self.training_timer.timeout.connect(self.add_training_data)
        self.gesture_list = []
        self.current_training_data_dict = {}
        self.update_gesture_list()

    def __init_ui(self):
        self.setWindowTitle("Drumkit")
        # Define a top-level widget to hold everything

        central_widget = QtGui.QWidget()
        central_widget.setFixedWidth(1000)
        self.setCentralWidget(central_widget)
        # Create a grid layout to manage the widgets size and position
        layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(layout)

        # Creating flowchart
        self.fc = Flowchart(terminals={})
        layout.addWidget(self.fc.widget())

        # create DIPPID node
        self.dippid_node0 = self.fc.createNode("DIPPID", pos=(0, 0))
        self.dippid_node1 = self.fc.createNode("DIPPID", pos=(0, 150))

        # create Train node
        self.train_node = self.fc.createNode("TrainNode", pos=(450, 150))

        # create Prediction node
        self.prediction_node0 = self.fc.createNode(
            "PredictionNode", pos=(450, 150))
        self.prediction_node1 = self.fc.createNode(
            "PredictionNode", pos=(450, 300))
        # create FFT node
        self.convolveNode0 = self.fc.createNode("ConvolveNode", pos=(300, 150))
        self.convolveNode1 = self.fc.createNode("ConvolveNode", pos=(300, 300))

        # init user input ui
        self.main_control_widget = QtWidgets.QWidget()
        self.main_control_widget.setFixedSize(800, 400)
        self.main_control_widget.setLayout(QtWidgets.QGridLayout())
        layout.addWidget(self.main_control_widget)

        # start connection error ui
        self.connection_error_widget = QtWidgets.QWidget()
        self.connection_error_widget.setFixedSize(200, 100)
        self.connection_error_widget.setLayout(QtWidgets.QVBoxLayout())
        self.connection_error_label = QtWidgets.QLabel()
        self.connection_error_label.setStyleSheet("QLabel {color: red;}")
        self.connection_error_widget.layout().addWidget(self.connection_error_label)
        self.main_control_widget.layout().addWidget(
            self.connection_error_widget, 2, 0, 1, 0)

        # start prediction ui
        self.prediction_control_widget = QtWidgets.QWidget()
        self.prediction_control_widget.setFixedSize(200, 100)
        self.prediction_control_widget.setLayout(QtWidgets.QVBoxLayout())
        self.predict_button = QtWidgets.QPushButton("Start Predicting")
        self.predict_button.clicked.connect(self.predict_button_press)
        self.predict_label = QtWidgets.QLabel("No Gesture Recognizes yet")
        self.prediction_control_widget.layout().addWidget(self.predict_button)
        self.prediction_control_widget.layout().addWidget(self.predict_label)
        self.main_control_widget.layout().addWidget(
            self.prediction_control_widget, 1, 0, 1, 1)

        # start training ui
        self.train_control_widget = QtWidgets.QWidget()
        self.train_control_widget.setFixedSize(200, 100)
        self.train_control_widget.setLayout(QtWidgets.QVBoxLayout())
        self.train_button = QtWidgets.QPushButton("Start Training")
        self.train_button.clicked.connect(self.train_button_press)
        self.train_name_input = QtWidgets.QLineEdit("Nothing")
        self.train_control_widget.layout().addWidget(self.train_name_input)
        self.train_control_widget.layout().addWidget(self.train_button)
        self.main_control_widget.layout().addWidget(
            self.train_control_widget, 0, 0, 1, 1)

        # start gesture list ui
        self.gesture_list_widget = QtWidgets.QWidget()
        self.gesture_list_widget.setFixedSize(200, 200)
        self.gesture_list_widget.setLayout(QtWidgets.QVBoxLayout())
        self.gesture_list_list_widget = QtWidgets.QListWidget()
        self.gesture_list_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.gesture_list_delete_button = QtWidgets.QPushButton(
            "Delete Selected")
        self.gesture_list_delete_button.clicked.connect(
            self.delete_selected_gesture_from_list)
        self.gesture_list_save_button = QtWidgets.QPushButton("Save Changes")
        self.gesture_list_save_button.clicked.connect(self.save_changes_to_csv)
        self.gesture_list_widget.layout().addWidget(self.gesture_list_list_widget)
        self.gesture_list_widget.layout().addWidget(self.gesture_list_delete_button)
        self.gesture_list_widget.layout().addWidget(self.gesture_list_save_button)
        self.main_control_widget.layout().addWidget(
            self.gesture_list_widget, 0, 1, 1, 1)

    def predict_button_press(self):
        if self.convolveNode0.get_had_input_yet():
            self.connection_error_label.setText("")
            if not self.is_predicting:
                self.update_prediction_node_data()
                self.prediction_timer.start(400)
                self.is_predicting = True
                self.predict_button.setText("Stop Predicting")
            else:
                self.prediction_timer.stop()
                self.is_predicting = False
                self.predict_button.setText("Start Predicting")
        else:
            self.connection_error_label.setText(
                "Dippid device not connected, please open 'Dippid.0' on the left side and connect")

    def update_prediction(self):
        self.predict_label.setText(
            f"Gesture: {self.prediction_node0.get_prediction()} + {self.prediction_node1.get_prediction()}")

    def init_logger(self, filename):
        self.current_filename = filename
        if os.path.isfile(filename):
            self.gesture_data = pd.read_csv(filename)
        else:
            self.gesture_data = pd.DataFrame(
                columns=['gestureName', 'frequenciesX', 'frequenciesY', 'frequenciesZ'])

    def train_button_press(self):
        if self.convolveNode0.get_had_input_yet():
            self.connection_error_label.setText("")
            self.training_timer.start(TIME_FOR_DATA)
            self.train_button.setText("Training!")
            self.train_button.setDisabled(True)
        else:
            self.connection_error_label.setText(
                "Dippid device not connected, please open 'Dippid.0' on the left side and connect")

    def add_training_data(self):
        self.training_timer.stop()
        self.gesture_data = self.gesture_data.append(
            {'gestureName': self.train_name_input.text(),
             'frequenciesX': self.train_node.get_current_frequencies_as_string("|")[0],
             'frequenciesY': self.train_node.get_current_frequencies_as_string("|")[1],
             'frequenciesZ': self.train_node.get_current_frequencies_as_string("|")[2]},
            ignore_index=True)
        print(self.gesture_data)
        self.gesture_data.to_csv(TRAINING_DATA_FILE, header=True, index=False, index_label=False)
        self.train_button.setDisabled(False)
        self.train_button.setText("Start Training")
        self.update_gesture_list()

    def update_gesture_list(self):
        self.gesture_list_list_widget.clear()
        self.gesture_list = []
        for index, row in self.gesture_data.iterrows():
            self.gesture_list.append(row["gestureName"])
        self.gesture_list_list_widget.insertItems(0, self.gesture_list)
        self.update_prediction_node_data()

    def delete_selected_gesture_from_list(self):
        index = self.gesture_list_list_widget.currentIndex().row()
        self.gesture_data = self.gesture_data.drop(
            self.gesture_data.index[index])
        # print(self.gesture_data)
        self.update_gesture_list()

    def save_changes_to_csv(self):
        self.gesture_data.to_csv(self.current_filename, index=False)

    def update_prediction_node_data(self):
        self.current_training_data_dict = {}
        for index, row in self.gesture_data.iterrows():
            gesture_name = row[0]
            gesture_x_frequencies = fromstring(row[1], sep="|")
            gesture_y_frequencies = fromstring(row[2], sep="|")
            gesture_z_frequencies = fromstring(row[3], sep="|")
            self.current_training_data_dict[gesture_name] = {
                "x": gesture_x_frequencies, "y": gesture_y_frequencies, "z": gesture_z_frequencies}
        self.prediction_node0.init_svm_with_data(
            self.current_training_data_dict)

    def init_nodes(self):
        # create buffer nodes
        buffer_node_x0 = self.fc.createNode("Buffer", pos=(150, 0))
        buffer_node_y0 = self.fc.createNode("Buffer", pos=(150, 150))
        buffer_node_z0 = self.fc.createNode("Buffer", pos=(150, 300))

        buffer_node_x1 = self.fc.createNode("Buffer", pos=(150, 450))
        buffer_node_y1 = self.fc.createNode("Buffer", pos=(150, 600))
        buffer_node_z1 = self.fc.createNode("Buffer", pos=(150, 750))

        # connect buffer nodes
        self.fc.connectTerminals(
            self.dippid_node0["accelX"], buffer_node_x0["dataIn"])
        self.fc.connectTerminals(
            self.dippid_node0["accelY"], buffer_node_y0["dataIn"])
        self.fc.connectTerminals(
            self.dippid_node0["accelZ"], buffer_node_z0["dataIn"])
        self.fc.connectTerminals(
            self.dippid_node1["accelX"], buffer_node_x1["dataIn"])
        self.fc.connectTerminals(
            self.dippid_node1["accelY"], buffer_node_y1["dataIn"])
        self.fc.connectTerminals(
            self.dippid_node1["accelZ"], buffer_node_z1["dataIn"])

        # connect convolution node
        self.fc.connectTerminals(
            buffer_node_x0["dataOut"], self.convolveNode0["accelX"])
        self.fc.connectTerminals(
            buffer_node_y0["dataOut"], self.convolveNode0["accelY"])
        self.fc.connectTerminals(
            buffer_node_z0["dataOut"], self.convolveNode0["accelZ"])
        self.fc.connectTerminals(
            buffer_node_x1["dataOut"], self.convolveNode1["accelX"])
        self.fc.connectTerminals(
            buffer_node_y1["dataOut"], self.convolveNode1["accelY"])
        self.fc.connectTerminals(
            buffer_node_z1["dataOut"], self.convolveNode1["accelZ"])

        # connect train node to accelerator values
        self.fc.connectTerminals(
            self.train_node["accelerator_x"], self.convolveNode0["frequencyX"])
        self.fc.connectTerminals(
            self.train_node["accelerator_y"], self.convolveNode0["frequencyY"])
        self.fc.connectTerminals(
            self.train_node["accelerator_z"], self.convolveNode0["frequencyZ"])
        self.fc.connectTerminals(
            self.prediction_node0["accelerator_x"], self.convolveNode0["frequencyX"])
        self.fc.connectTerminals(
            self.prediction_node0["accelerator_y"], self.convolveNode0["frequencyY"])
        self.fc.connectTerminals(
            self.prediction_node0["accelerator_z"], self.convolveNode0["frequencyZ"])
        self.fc.connectTerminals(
            self.prediction_node1["accelerator_x"], self.convolveNode1["frequencyX"])
        self.fc.connectTerminals(
            self.prediction_node1["accelerator_y"], self.convolveNode1["frequencyY"])
        self.fc.connectTerminals(
            self.prediction_node1["accelerator_z"], self.convolveNode1["frequencyZ"])


class PredictionNode(Node):
    counter = 0
    nodeName = "PredictionNode"
    fs = fluidsynth.Synth(1)
    fs.start(driver='alsa')
    sfid = fs.sfload('./pns_drum.sf2')
    # select MIDI track, sound font, MIDI bank and preset
    fs.program_select(0, sfid, 0, 0)

    def __init__(self, name):
        Node.__init__(self, name, terminals={
            "accelerator_x": dict(io="in"),
            "accelerator_y": dict(io="in"),
            "accelerator_z": dict(io="in")
        })

        self.current_gesture_x_frequencies = []
        self.current_gesture_y_frequencies = []
        self.current_gesture_z_frequencies = []
        self.current_prediction = "None"
        self.training_data_dict = {}

    def init_svm_with_data(self, data):
        print("initsvm with data")
        # print(data)
        self.training_data_dict = data
        self.classifier = svm.SVC()
        categories = []
        training_data = []
        if len(data) > 1:
            current_index = 0
            for key, value in data.items():
                categories += [current_index]
                current_values_array = []
                current_values_array.append(value.get("x"))
                current_values_array.append(value.get("y"))
                current_values_array.append(value.get("z"))

                training_data += self.get_svm_data_array(current_values_array)

                current_index += 1
            self.classifier.fit(training_data, categories)

    def get_svm_data_array(self, x_y_z_array):
        svm_data_array = []
        for value in x_y_z_array:
            x_cut = []
            for index, x_value in enumerate(x_y_z_array[0]):
                if index < DATA_LENGTH:
                    x_cut.append(x_value)
            y_cut = []
            for index, y_value in enumerate(x_y_z_array[1]):
                if index < DATA_LENGTH:
                    y_cut.append(y_value)
            z_cut = []
            for index, z_value in enumerate(x_y_z_array[2]):
                if index < DATA_LENGTH:
                    z_cut.append(z_value)

            svm_data_array += x_cut + y_cut + z_cut
        return [svm_data_array]

    # testing sound accuracy
    def make_sound(self, result):
        if (result > 0):
            self.fs.noteon(0, 35, 100)
            self.fs.noteoff(0, 35)

    def get_prediction(self):
        input_data = []
        input_data.append(self.current_gesture_x_frequencies)
        input_data.append(self.current_gesture_y_frequencies)
        input_data.append(self.current_gesture_z_frequencies)
        predicition_data = self.get_svm_data_array(input_data)
        result = self.classifier.predict(predicition_data)[0]
        self.make_sound(result)
        return list(self.training_data_dict.keys())[result]

    def process(self, **kwds):
        # Get the last values from our accelerator data
        self.current_gesture_x_frequencies = kwds["accelerator_x"]
        self.current_gesture_y_frequencies = kwds["accelerator_y"]
        self.current_gesture_z_frequencies = kwds["accelerator_z"]


class TrainNode(Node):
    nodeName = "TrainNode"

    def __init__(self, name):
        Node.__init__(self, name, terminals={
            "accelerator_x": dict(io="in"),
            "accelerator_y": dict(io="in"),
            "accelerator_z": dict(io="in")
        })
        self.isRecording = False
        self.current_gesture_x_frequencies = []
        self.current_gesture_y_frequencies = []
        self.current_gesture_z_frequencies = []

    def get_current_frequencies_as_string(self, seperator):
        current_frequency_strings = []
        current_frequency_strings.append(seperator.join(
            map(str, self.current_gesture_x_frequencies)))
        current_frequency_strings.append(seperator.join(
            map(str, self.current_gesture_y_frequencies)))
        current_frequency_strings.append(seperator.join(
            map(str, self.current_gesture_z_frequencies)))
        return current_frequency_strings

    def process(self, **kwds):
        # Get the last values from our accelerator data
        self.current_gesture_x_frequencies = kwds["accelerator_x"]
        self.current_gesture_y_frequencies = kwds["accelerator_y"]
        self.current_gesture_z_frequencies = kwds["accelerator_z"]


if __name__ == "__main__":
    # fclib.registerNodeType(ConvolveNode, [("ConvolveNode",)])
    fclib.registerNodeType(TrainNode, [("TrainNode",)])
    fclib.registerNodeType(PredictionNode, [("PredictionNode",)])
    app = QtWidgets.QApplication([])
    win = Drumkit()

    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        sys.exit(app.exec_())

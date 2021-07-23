#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
# Script was written by Erik Blank and Michael Schmidt

import sys
from PyQt5 import uic, QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from pyqtgraph.flowchart import Flowchart, Node
from DIPPID_pyqtnode import DIPPIDNode, BufferNode
import pyqtgraph.flowchart.library as fclib
import pandas as pd
import os
from numpy import fromstring
import time
from ConvolutionNode import ConvolveNode
from TrainingNode import TrainNode
from PredictionNode import PredictNode
from RecordAudio import RecordAudio
import fluidsynth
import numpy

# Filename where our gestures are saved
TRAINING_DATA_FILE = "training_data.csv"

# The amount of transformed signals from the dippid we use for 1 gesture;
# the transfomation cuts the dippid signal amount in half
# to calculate to time per gesture do:
# DATA_LENGTH / (DippidFrequency * 2)
DATA_LENGTH = 30

# 30 sec training time per gesture
TIME_FOR_DATA = 30000


class Drumkit(QtWidgets.QMainWindow):

    DRUMS = {
        "Bass/Kick drum": 35,
        "Snare drum": 38,
        "Hi-hat Cymbal": 46,
        "Crash Cymbal": 49,
        "Tom drum 1": 45,
        "Tom drum 2": 50,
        "Ride Cymbal": 51,
        "Floor Tom drum": 41
    }

    def __init__(self):
        super(Drumkit, self).__init__()
        self.comboboxes_device1 = []
        self.comboboxes_device2 = []
        # button 1, 2, 3 for each device
        self.current_btn_device0 = 0
        self.current_drum_device0 = 35
        self.current_btn_device1 = 0
        self.current_drum_device1 = 35
        self.recorder = RecordAudio()
        self.initUI()
        self.init_logger(TRAINING_DATA_FILE)
        self.init_nodes()
        self.is_predicting0 = False
        self.prediction_timer0 = QtCore.QTimer()
        self.prediction_timer0.timeout.connect(self.update_prediction_device0)
        self.is_predicting1 = False
        self.prediction_timer1 = QtCore.QTimer()
        self.prediction_timer1.timeout.connect(self.update_prediction_device1)
        self.gesture_list = []
        self.current_training_data_dict = {}
        self.connectButtons()

    def initUI(self):
        # create DIPPID nodes
        central_widget = QtGui.QWidget()
        central_widget.setFixedWidth(1000)
        self.setCentralWidget(central_widget)

        # Create a grid layout to manage the widgets size and position
        layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(layout)

        # Creating flowchart
        self.fc = Flowchart(terminals={})
        layout.addWidget(self.fc.widget())

        self.dippid_node0 = self.fc.createNode("DIPPID", pos=(0, 0))
        self.dippid_node1 = self.fc.createNode("DIPPID", pos=(0, 150))

        self.ui = uic.loadUi("user_interface.ui", self)
        self.setWindowTitle("Drumkit Demo")

        # set items for the comboboxes
        self.comboboxes_device1.append(self.ui.comboBox_1_1)
        self.comboboxes_device1.append(self.ui.comboBox_1_2)
        self.comboboxes_device1.append(self.ui.comboBox_1_3)

        self.comboboxes_device2.append(self.ui.comboBox_2_1)
        self.comboboxes_device2.append(self.ui.comboBox_2_2)
        self.comboboxes_device2.append(self.ui.comboBox_2_3)
        for cb in self.comboboxes_device1:
            cb.addItems(self.DRUMS)

        for cb in self.comboboxes_device2:
            cb.addItems(self.DRUMS)

        # put labels for device-buttons in a list to highlight later
        self.device0_btn_labels = []
        self.device0_btn_labels.append(self.ui.label_btnDevice1_1)
        self.device0_btn_labels.append(self.ui.label_btnDevice1_2)
        self.device0_btn_labels.append(self.ui.label_btnDevice1_3)

        self.device2_btn_labels = []
        self.device2_btn_labels.append(self.ui.label_btnDevice2_1)
        self.device2_btn_labels.append(self.ui.label_btnDevice2_2)
        self.device2_btn_labels.append(self.ui.label_btnDevice2_3)

        # create Train node
        self.train_node0 = self.fc.createNode("TrainNode", pos=(450, 150))
        self.train_node1 = self.fc.createNode("TrainNode", pos=(450, 300))

        # create Prediction node
        self.prediction_node0 = self.fc.createNode(
            "PredictNode", pos=(450, 150))
        self.prediction_node1 = self.fc.createNode(
            "PredictNode", pos=(450, 300))
        # create FFT node
        self.convolveNode0 = self.fc.createNode("ConvolveNode", pos=(300, 150))
        self.convolveNode1 = self.fc.createNode("ConvolveNode", pos=(300, 300))

        self.show()

    def connectButtons(self):
        # buttons to connect devices
        self.ui.btnConnect0.clicked.connect(lambda x: self.__connectDevice1())
        self.ui.btnConnect1.clicked.connect(lambda x: self.__connectDevice2())

        # buttons for audio section
        self.ui.btn_start_record.clicked.connect(
            lambda x: self.__start_record())
        self.ui.btn_stop_record.clicked.connect(lambda x: self.__stop_record())
        self.ui.btn_play_selected.clicked.connect(
            lambda x: self.__play_selected())
        self.ui.btn_play_all.clicked.connect(lambda x: self.__play_all())
        self.ui.btn_delete_selected.clicked.connect(
            lambda x: self.__remove_selected())
        self.ui.btn_delete_all.clicked.connect(lambda x: self.__remove_all())
        self.ui.btn_undo.clicked.connect(lambda x: self.__undo())
        self.ui.btn_export.clicked.connect(lambda x: self.__export())
        self.ui.btn_add_audio.clicked.connect(lambda x: self.__add_audio())

        # buttons to start playing each device
        self.ui.btnStartPrediction0.clicked.connect(
            lambda x: self.predict_button_press_device0())
        self.ui.btnStartPrediction1.clicked.connect(
            lambda x: self.predict_button_press_device1())

    def __connectDevice1(self):
        port = int(self.ui.lineEditPort0.text())
        hz = int(self.ui.lineEditConnect0.text())
        print(f'connect device 1 with {hz}hz')
        self.dippid_node0.connect_device(port, hz)
        self.btnConnect0.setText("Connected")
        self.btnConnect0.setDisabled(True)

    def __connectDevice2(self):
        port = int(self.ui.lineEditPort1.text())
        hz = int(self.ui.lineEditConnect1.text())
        print(f'connect device 2 with {hz}hz')
        self.dippid_node1.connect_device(port, hz)
        self.btnConnect1.setText("Connected")
        self.btnConnect1.setDisabled(True)

    # TODO: implement method
    def __start_record(self):
        if self.is_predicting0:
            self.prediction_node0.start_recording()
        if self.is_predicting1:
            self.prediction_node1.start_recording()

    # TODO: implement method
    def __stop_record(self):
        if self.is_predicting0:
            self.prediction_node0.stop_recording()
        if self.is_predicting1:
            self.prediction_node1.stop_recording()
        self.recorder.add_record(self.prediction_node0.get_recording())
        self.ui.listRecordings.clear()
        self.ui.listRecordings.addItems(self.recorder.get_audios())

    def __play_selected(self):
        index = self.ui.listRecordings.currentRow()
        if index != -1:
            self.recorder.play(index)
        else:
            print("no file selected")

    def __play_all(self):
        self.recorder.play_all()

    def __remove_selected(self):
        index = self.ui.listRecordings.currentRow()
        if index != -1:
            self.recorder.remove_one(index)
            self.ui.listRecordings.takeItem(index)
        else:
            print("no file selected")

    def __remove_all(self):
        self.ui.listRecordings.clear()
        self.recorder.remove_all()

    def __undo(self):
        self.recorder.undo()
        self.ui.listRecordings.clear()
        self.ui.listRecordings.addItems(self.recorder.get_audios())

    # TODO: implement method
    def __export(self):
        self.recorder.export_record()

    # TODO: delete this method, its just for testing
    def __add_audio(self):
        s = []
        fl = fluidsynth.Synth()

        # Initial silence is 1 second
        s = numpy.append(s, fl.get_samples(44100 * 1))
        fl.start(driver='alsa')
        sfid = fl.sfload('./pns_drum.sf2')
        fl.program_select(0, sfid, 0, 0)

        fl.noteon(0, 35, 100)

        # Chord is held for 2 seconds
        for i in range(8):
            s = numpy.append(s, fl.get_samples(int(44100 * 0.1)))
            fl.noteon(0, 38, 100)
            fl.noteon(0, 46, 100)

        # Chord is held for 2 seconds
        s = numpy.append(s, fl.get_samples(44100 * 1))

        fl.noteon(0, 46, 100)

        # Decay of chord is held for 1 second
        s = numpy.append(s, fl.get_samples(44100 * 1))

        fl.delete()

        self.recorder.add_record(fluidsynth.raw_audio_string(s))
        self.ui.listRecordings.addItem(self.recorder.get_audios()[-1])

    def predict_button_press_device0(self):
        if self.convolveNode0.get_had_input_yet():
            self.errorLabel0.setText("")
            if not self.is_predicting0:
                self.update_prediction_node_data()
                self.prediction_timer0.start(400)
                self.is_predicting0 = True
                self.btnStartPrediction0.setText("Stop Playing.")
                self.highlight_labels(0,1)
            else:
                self.prediction_timer0.stop()
                self.is_predicting0 = False
                self.btnStartPrediction0.setText("Start Playing! (Device 1)")
                self.unhighlight_labels(0)
        else:
            self.errorLabel0.setText(
                "Err! Connect Device first.")

    def predict_button_press_device1(self):
        if self.convolveNode1.get_had_input_yet():
            self.errorLabel1.setText("")
            if not self.is_predicting1:
                self.update_prediction_node_data()
                self.prediction_timer1.start(400)
                self.is_predicting1 = True
                self.btnStartPrediction1.setText("Stop Playing.")
                self.highlight_labels(1,1)
            else:
                self.prediction_timer1.stop()
                self.is_predicting1 = False
                self.btnStartPrediction1.setText("Start Playing! (Device 2)")
                self.unhighlight_labels(1)
        else:
            self.errorLabel1.setText(
                "Err! Connect Device first.")

    def handle_btns_device0(self, btns):
        if (btns["button1"] == 1):
            self.current_btn_device0 = 1
            self.current_drum_device0 = self.DRUMS[self.comboBox_1_1.currentText(
            )]
            self.unhighlight_labels(0)
            self.highlight_labels(0, 1)
        elif (btns["button2"] == 1):
            self.current_btn_device0 = 2
            self.current_drum_device0 = self.DRUMS[self.comboBox_1_2.currentText(
            )]
            self.unhighlight_labels(0)
            self.highlight_labels(0, 2)
        elif (btns["button3"] == 1):
            self.current_btn_device0 = 3
            self.current_drum_device0 = self.DRUMS[self.comboBox_1_3.currentText(
            )]
            self.unhighlight_labels(0)
            self.highlight_labels(0, 3)

    def handle_btns_device1(self, btns):
        if (btns["button1"] == 1):
            self.current_btn_device1 = 1
            self.current_drum_device1 = self.DRUMS[self.comboBox_2_1.currentText(
            )]
            self.unhighlight_labels(1)
            self.highlight_labels(1, 1)
        elif (btns["button2"] == 1):
            self.current_btn_device1 = 2
            self.current_drum_device1 = self.DRUMS[self.comboBox_2_2.currentText(
            )]
            self.unhighlight_labels(1)
            self.highlight_labels(1, 2)
        elif (btns["button3"] == 1):
            self.current_btn_device1 = 3
            self.current_drum_device1 = self.DRUMS[self.comboBox_2_3.currentText(
            )]
            self.unhighlight_labels(1)
            self.highlight_labels(1, 3)

    def update_prediction_device0(self):
        self.handle_btns_device0(self.dippid_node0.get_btns())
        self.prediction_node0.get_prediction(self.current_drum_device0)

    def update_prediction_device1(self):
        self.handle_btns_device1(self.dippid_node1.get_btns())
        self.prediction_node1.get_prediction(self.current_drum_device1)

    def init_logger(self, filename):
        self.current_filename = filename
        if os.path.isfile(filename):
            self.gesture_data = pd.read_csv(filename)
        else:
            self.gesture_data = pd.DataFrame(
                columns=['gestureName', 'frequenciesX', 'frequenciesY', 'frequenciesZ'])

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
        self.prediction_node1.init_svm_with_data(
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
            self.train_node0["accelerator_x"], self.convolveNode0["frequencyX"])
        self.fc.connectTerminals(
            self.train_node0["accelerator_y"], self.convolveNode0["frequencyY"])
        self.fc.connectTerminals(
            self.train_node0["accelerator_z"], self.convolveNode0["frequencyZ"])
        self.fc.connectTerminals(
            self.train_node1["accelerator_x"], self.convolveNode1["frequencyX"])
        self.fc.connectTerminals(
            self.train_node1["accelerator_y"], self.convolveNode1["frequencyY"])
        self.fc.connectTerminals(
            self.train_node1["accelerator_z"], self.convolveNode1["frequencyZ"])

        # connect prediction nodes to accelerator values
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

    def get_selected_drum(self, device_num, btn_num):
        if device_num == 1:
            self.comboboxes_device1[btn_num - 1].currentText()
        elif device_num == 2:
            return self.comboboxes_device2[btn_num - 1].currentText()

    # highlight labels if button is active
    def highlight_labels(self, device_num, btn_num):
        # hightlight label
        if device_num == 0:
            self.device0_btn_labels[btn_num -
                                    1].setStyleSheet("background-color: lightgreen")
        elif device_num == 1:
            self.device2_btn_labels[btn_num -
                                    1].setStyleSheet("background-color: lightgreen")

    def unhighlight_labels(self, device_num):
        # set background of all labels to transparent
        if device_num == 0:
            for label in self.device0_btn_labels:
                label.setStyleSheet("background-color: transparent")
        elif device_num == 1:
            for label in self.device2_btn_labels:
                label.setStyleSheet("background-color: transparent")


fclib.registerNodeType(ConvolveNode, [("ConvolveNode",)])
fclib.registerNodeType(TrainNode, [("TrainingNode",)])
fclib.registerNodeType(PredictNode, [("PredictionNode",)])


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = Drumkit()

    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        sys.exit(app.exec_())

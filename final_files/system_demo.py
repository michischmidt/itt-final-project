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

# Filename where our gestures are saved
TRAINING_DATA_FILE = "training_data.csv"

# The amount of transformed signals from the dippid we use for 1 gesture;
# the transfomation cuts the dippid signal amount in half
# to calculate to time per gesture do:
# DATA_LENGTH / (DippidFrequency * 2)
DATA_LENGTH = 30
TIME_FOR_DATA = 30000


class Drumkit(QtWidgets.QMainWindow):
    def __init__(self):
        super(Drumkit, self).__init__()
        self.drums = ["drum1", "drum2", "drum3"]
        self.comboboxes_device1 = []
        self.comboboxes_device2 = []
        self.dippid0_btn1 = 1
        self.dippid0_btn2 = 0
        self.dippid0_btn3 = 0
        self.dippid1_btn1 = 1
        self.dippid1_btn2 = 0
        self.dippid1_btn3 = 0
        self.initUI()
        self.init_logger(TRAINING_DATA_FILE)
        self.init_nodes()
        self.is_predicting = False
        self.prediction_timer = QtCore.QTimer()
        self.prediction_timer.timeout.connect(self.update_prediction)
        self.gesture_list = []
        self.current_training_data_dict = {}
        self.connectButtons()

    # TODO: Give port from UI
    # TODO: Disable connect buttons after connected (siehe DIPPID_pyqtnode)
    # TODO: Connect buttons properly
    # TODO: Convert btn string 1/0 into int before intilizing self.dippid0_btn
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
        self.setWindowTitle("Drumkit")

        # set items for the comboboxes
        self.comboboxes_device1.append(self.ui.comboBox_1_1)
        self.comboboxes_device1.append(self.ui.comboBox_1_2)
        self.comboboxes_device1.append(self.ui.comboBox_1_3)

        self.comboboxes_device2.append(self.ui.comboBox_2_1)
        self.comboboxes_device2.append(self.ui.comboBox_2_2)
        self.comboboxes_device2.append(self.ui.comboBox_2_3)
        for cb in self.comboboxes_device1:
            cb.addItems(self.drums)

        for cb in self.comboboxes_device2:
            cb.addItems(self.drums)

        # put labels for device-buttons in a list to highlight later
        self.device1_btn_labels = []
        self.device1_btn_labels.append(self.ui.label_btnDevice1_1)
        self.device1_btn_labels.append(self.ui.label_btnDevice1_2)
        self.device1_btn_labels.append(self.ui.label_btnDevice1_3)

        self.device2_btn_labels = []
        self.device2_btn_labels.append(self.ui.label_btnDevice2_1)
        self.device2_btn_labels.append(self.ui.label_btnDevice2_2)
        self.device2_btn_labels.append(self.ui.label_btnDevice2_3)

        # create Train node
        self.train_node = self.fc.createNode("TrainNode", pos=(450, 150))

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
        self.ui.btnConnect1.clicked.connect(lambda x: self.__connectDevice1())
        self.ui.btnConnect2.clicked.connect(lambda x: self.__connectDevice2())

        # buttons to start playing each device
        self.ui.btnStartPrediction0.clicked.connect(
            lambda x: self.predict_button_press(self.convolveNode0, self.errorLabel0, self.btnStartPrediction0))
        self.ui.btnStartPrediction1.clicked.connect(
            lambda x: self.predict_button_press(self.convolveNode1, self.errorLabel1, self.btnStartPrediction1))

    def __connectDevice1(self):
        hz_device_1 = self.ui.lineEditConnect1.text()
        print(f'connect device 1 with {hz_device_1}hz')
        self.dippid_node0.connect_device(5700, 30)

    def __connectDevice2(self):
        hz_device_2 = self.ui.lineEditConnect2.text()
        print(f'connect device 2 with {hz_device_2}hz')
        self.dippid_node1.connect_device(5701, 30)

    def predict_button_press(self, convolveNode, errorLabel, btn):
        if convolveNode.get_had_input_yet():
            errorLabel.setText("")
            if not self.is_predicting:
                self.update_prediction_node_data()
                self.prediction_timer.start(400)
                self.is_predicting = True
                btn.setText("Stop Playing.")
            else:
                self.prediction_timer.stop()
                self.is_predicting = False
                btn.setText("Start Playing again!")
        else:
            errorLabel.setText(
                "Dippid device not connected, please try again to connect your first Device")

    def update_prediction(self):
        self.prediction_node0.get_prediction()
        self.prediction_node1.get_prediction()

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

    def get_selected_drum(self, device_num, btn_num):
        if device_num == 1:
            self.comboboxes_device1[btn_num - 1].currentText()
        elif device_num == 2:
            return self.comboboxes_device2[btn_num - 1].currentText()

    # highlight labels if button is active
    def highlight_labels(self, device_num, btn_num):
        # set background of all labels to transparent
        for label in self.device1_btn_labels:
            label.setStyleSheet("background-color: transparent")
        for label in self.device2_btn_labels:
            label.setStyleSheet("background-color: transparent")

        # hightlight label
        if device_num == 1:
            self.device1_btn_labels[btn_num -
                                    1].setStyleSheet("background-color: lightgreen")
        elif device_num == 2:
            self.device1_btn_labels[btn_num -
                                    1].setStyleSheet("background-color: lightgreen")

    def unhighlight_labels(self):
        # set background of all labels to transparent
        for label in self.device1_btn_labels:
            label.setStyleSheet("background-color: transparent")
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
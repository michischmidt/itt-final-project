import sys
from PyQt5 import uic, QtCore, QtWidgets, QtGui


class DrumkitUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.drums = ["drum1", "drum2", "drum3"]
        self.comboboxes_device1 = []
        self.comboboxes_device2 = []
        self.initUI()
        self.connectButtons()

    def initUI(self):
        self.ui = uic.loadUi("user_interface.ui", self)
        # allow only ints for lineEdits in "Devices" sector
        self.onlyInt = QtGui.QIntValidator()
        self.ui.lineEditConnect1.setValidator(self.onlyInt)
        self.ui.lineEditConnect2.setValidator(self.onlyInt)

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

        self.show()

    def connectButtons(self):
        # buttons to connect devices
        self.ui.btnConnect1.clicked.connect(lambda x: self.__connectDevice1())
        self.ui.btnConnect2.clicked.connect(lambda x: self.__connectDevice2()) 
    
    def __connectDevice1(self):
        hz_device_1 = self.ui.lineEditConnect1.text()
        print(f'connect device 1 with {hz_device_1}hz')

    def __connectDevice2(self):
        hz_device_2 = self.ui.lineEditConnect2.text()
        print(f'connect device 2 with {hz_device_2}hz')

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
            self.device1_btn_labels[btn_num - 1].setStyleSheet("background-color: lightgreen")
        elif device_num == 2:
            self.device1_btn_labels[btn_num - 1].setStyleSheet("background-color: lightgreen")

    def unhighlight_labels(self):
        # set background of all labels to transparent
        for label in self.device1_btn_labels:
            label.setStyleSheet("background-color: transparent")
        for label in self.device2_btn_labels:
            label.setStyleSheet("background-color: transparent")

    


def main():
    app = QtWidgets.QApplication(sys.argv)
    drumkitUI = DrumkitUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
# Script was rewritten by Erik Blank and Michael Schmidt

from pyqtgraph.flowchart import Flowchart, Node
from pyqtgraph.flowchart.library.common import CtrlNode
import pyqtgraph.flowchart.library as fclib
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from DIPPID import SensorUDP, SensorSerial, SensorWiimote
import sys
from FFTNode import FftNode
from ConvolutionNode import ConvolveNode


class BufferNode(Node):
    """
    Buffers the last n samples provided on input and provides
    them as a list of length n on output.
    A spinbox widget allows for setting the size of the buffer.
    Default size is 32 samples.
    """
    nodeName = "Buffer"

    def __init__(self, name):
        terminals = {
            'dataIn': dict(io='in'),
            'dataOut': dict(io='out'),
        }

        self.buffer_size = 32
        self._buffer = np.array([])
        Node.__init__(self, name, terminals=terminals)

    def process(self, **kwds):
        self._buffer = np.append(
            self._buffer, kwds['dataIn'])[-self.buffer_size:]

        return {'dataOut': self._buffer}


fclib.registerNodeType(BufferNode, [('Data',)])


class DIPPIDNode(Node):
    """
    Outputs sensor data from DIPPID supported hardware.

    Supported sensors: accelerometer (3 axis)
    Text input box allows for setting a Bluetooth MAC address or Port.
    Pressing the "connect" button tries connecting to the DIPPID device.
    Update rate can be changed via a spinbox widget. Setting it to "0"
    activates callbacks every time a new sensor value arrives (which is
    quite often -> performance hit)
    """

    nodeName = "DIPPID"

    def __init__(self, name):
        terminals = {
            'accelX': dict(io='out'),
            'accelY': dict(io='out'),
            'accelZ': dict(io='out'),
        }

        self.dippid = None
        self._acc_vals = []
        self._btns = {
            "button1": 0,
            "button2": 0,
            "button3": 0
        }

        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)

        Node.__init__(self, name, terminals=terminals)

    def update_all_sensors(self):
        if self.dippid is None or not self.dippid.has_capability('accelerometer'):
            return
        if self.dippid is None or not self.dippid.has_capability('button_1'):
            return
        if self.dippid is None or not self.dippid.has_capability('button_2'):
            return
        if self.dippid is None or not self.dippid.has_capability('button_3'):
            return

        v = self.dippid.get_value('accelerometer')
        self._acc_vals = [v['x'], v['y'], v['z']]

        self._btns["button1"] = int(self.dippid.get_value('button_1'))
        self._btns["button2"] = int(self.dippid.get_value('button_2'))
        self._btns["button3"] = int(self.dippid.get_value('button_3'))

        self.update()

    def update_accel(self, acc_vals):
        if not self.dippid.has_capability('accelerometer'):
            return

        self._acc_vals = [acc_vals['x'], acc_vals['y'], acc_vals['z']]
        self.update()

    def connect_device(self, port, hz):
        address = str(port)

        if '/dev/tty' in address:  # serial tty
            self.dippid = SensorSerial(address)
        elif ':' in address:
            self.dippid = SensorWiimote(address)
        elif address.isnumeric():
            self.dippid = SensorUDP(int(address))
        else:
            print(f'invalid address: {address}')
            print('allowed types: UDP port, bluetooth address, path to /dev/tty*')

        if self.dippid is None:
            print("try again")
            return

        self.set_update_rate(hz)

    def set_update_rate(self, rate):
        if self.dippid is None:
            return

        self.dippid.unregister_callback('accelerometer', self.update_accel)

        if rate == 0:
            self.update_timer.stop()
        else:
            self.update_timer.start(int(1000 / rate))

    def get_btns(self):
        return self._btns

    def process(self, **kwdargs):
        return {'accelX': np.array([self._acc_vals[0]]),
                'accelY': np.array([self._acc_vals[1]]),
                'accelZ': np.array([self._acc_vals[2]])}


fclib.registerNodeType(DIPPIDNode, [('Sensor',)])
fclib.registerNodeType(FftNode, [("FftNode",)])

# Following functions are for singnal prcoessing visualization


def xPlot(fc, node, dippidNode, xPos):
    pw1 = pg.PlotWidget()
    layout.addWidget(pw1, xPos, 1)
    pw1.setYRange(0, 1)

    pw1Node = fc.createNode('PlotWidget', pos=(0, -150))
    pw1Node.setPlot(pw1)

    bufferNodeX = fc.createNode('Buffer', pos=(150, 0))

    fc.connectTerminals(dippidNode['accelX'], bufferNodeX['dataIn'])
    fc.connectTerminals(bufferNodeX['dataOut'], pw1Node['In'])

    pw2 = pg.PlotWidget()
    layout.addWidget(pw2, xPos, 2)
    pw2.setYRange(0, 1)

    pw2Node = fc.createNode('PlotWidget', pos=(0, -300))
    pw2Node.setPlot(pw2)

    fc.connectTerminals(bufferNodeX['dataOut'], node['accelX'])
    fc.connectTerminals(node['frequencyX'], pw2Node['In'])


def yPlot(fc, node, dippidNode, xPos):
    pw1 = pg.PlotWidget()
    layout.addWidget(pw1, xPos, 1)
    pw1.setYRange(0, 1)

    pw1Node = fc.createNode('PlotWidget', pos=(0, -150))
    pw1Node.setPlot(pw1)

    bufferNodeY = fc.createNode('Buffer', pos=(150, 0))

    fc.connectTerminals(dippidNode['accelY'], bufferNodeY['dataIn'])
    fc.connectTerminals(bufferNodeY['dataOut'], pw1Node['In'])

    pw2 = pg.PlotWidget()
    layout.addWidget(pw2, xPos, 2)
    pw2.setYRange(0, 1)

    pw2Node = fc.createNode('PlotWidget', pos=(0, -300))
    pw2Node.setPlot(pw2)

    fc.connectTerminals(bufferNodeY['dataOut'], node['accelY'])
    fc.connectTerminals(node['frequencyY'], pw2Node['In'])


def zPlot(fc, node, dippidNode, xPos):
    pw1 = pg.PlotWidget()
    layout.addWidget(pw1, xPos, 1)
    pw1.setYRange(0, 1)

    pw1Node = fc.createNode('PlotWidget', pos=(0, -150))
    pw1Node.setPlot(pw1)

    bufferNodeZ = fc.createNode('Buffer', pos=(150, 0))

    fc.connectTerminals(dippidNode['accelZ'], bufferNodeZ['dataIn'])
    fc.connectTerminals(bufferNodeZ['dataOut'], pw1Node['In'])

    pw2 = pg.PlotWidget()
    layout.addWidget(pw2, xPos, 2)
    pw2.setYRange(0, 1)

    pw2Node = fc.createNode('PlotWidget', pos=(0, -300))
    pw2Node.setPlot(pw2)

    fc.connectTerminals(bufferNodeZ['dataOut'], node['accelZ'])
    fc.connectTerminals(node['frequencyZ'], pw2Node['In'])


if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.setWindowTitle('DIPPIDNode demo')
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    layout = QtGui.QGridLayout()
    cw.setLayout(layout)

    # Create an empty flowchart with a single input and output
    fc = Flowchart(terminals={})
    w = fc.widget()

    layout.addWidget(fc.widget(), 0, 0, 2, 1)
    dippidNode = fc.createNode("DIPPID", pos=(0, 0))
    fftNode = fc.createNode("FftNode", pos=(0, 150))
    convolveNode = fc.createNode("ConvolveNode", pos=(0, 300))
    # xPlot(fc, fftNode, dippidNode, 0)
    # yPlot(fc, fftNode, dippidNode, 1)
    # zPlot(fc, fftNode, dippidNode, 2)
    xPlot(fc, convolveNode, dippidNode, 0)
    yPlot(fc, convolveNode, dippidNode, 1)
    zPlot(fc, convolveNode, dippidNode, 2)

    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        sys.exit(QtGui.QApplication.instance().exec_())

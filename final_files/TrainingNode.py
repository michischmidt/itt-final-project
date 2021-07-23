#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
# Script was written by Erik Blank and Michael Schmidt

from pyqtgraph.flowchart import Node


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

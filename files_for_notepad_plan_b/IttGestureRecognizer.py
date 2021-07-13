#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-
# Script was written by Johannes Lorper and Michael Schmidt

import sys
import os
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMainWindow
from QDrawWidget import QDrawWidget
import numpy as np


class IttGestureRecognizer(QMainWindow):
    def __init__(self):
        super(IttGestureRecognizer, self).__init__()
        self.draw_widget_width = 800
        self.draw_widget_height = 800
        self._init_ui()
        self.step_count = 64
        self.gesture_original = []
        self.gesture_resampled = []
        self.saved_gestures = {}

    def _init_ui(self):
        self.setWindowTitle("$1 Gesture Recognizer")
        self.__ui = uic.loadUi("GestureRecognition.ui", self)
        self._drawWidget = QDrawWidget()
        self._drawWidget.setFixedSize(
            self.draw_widget_width, self.draw_widget_height)
        # self._drawWidget.backgroundRole("#ffffff")
        self.__ui.DrawWidgetContainer.addWidget(self._drawWidget)
        self.__ui.SaveGestureButton.clicked.connect(self.save_current_gesture)
        self.__ui.ShowButton.clicked.connect(self.predict_gesture)
        self.__ui.DeleteButton.clicked.connect(self.delete_gesture)

    def delete_gesture(self):
        key = self.GestureList.currentItem().text()
        del self.saved_gestures[key]
        self.GestureList.clear()
        self.GestureList.insertItems(0, self.saved_gestures)

    def predict_gesture(self):
        self.gesture_original = self._drawWidget.points

        # iterate through saved gestures and calculate the dist against them
        resultText = ""
        lowest_dist = 0
        for key, value in self.saved_gestures.items():
            dist = 0
            for p1, p2 in zip(self.normalize(self.gesture_original), value):
                dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
                dist += dist
            dist = dist.item(0)

            if (lowest_dist == 0):
                lowest_dist = dist
                resultText = key

            if (dist < lowest_dist):
                lowest_dist = dist
                resultText = key

        # display result
        self.ResultOutput.setText("Result: " + resultText)

    def save_current_gesture(self):
        # resample, rotate and scale points
        self.gesture_original = self._drawWidget.points
        self.gesture_resampled = self.normalize(self.gesture_original)

        # save gesture and add it to ui
        self.saved_gestures[self.GestureNameInput.text()
                            ] = self.gesture_resampled
        gesture_name_list = []
        for key, value in self.saved_gestures.items():
            gesture_name_list.append(key)
        self.GestureList.clear()
        self.GestureList.insertItems(0, gesture_name_list)
        # TODO: remove, just for testing
        # self._drawWidget.points = self.gesture_resampled
        # self._drawWidget.repaint()

    def normalize(self, points):
        # 1. Resample point path
        resampled_points = self.resample(points)

        # 2. Calculate angle and rotate points
        angle = -self.angle_between(
            resampled_points[0], self.centroid(resampled_points))
        rotated_points = self.rotate(
            resampled_points, self.centroid(resampled_points), angle)

        # 3. Scale and translate
        scaled_points = self.scale(rotated_points)

        return scaled_points

    def distance(self, p1, p2):
        # basic vector norm

        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]

        return np.sqrt(dx * dx + dy * dy)

    def total_length(self, point_list):
        # calculate the sum of the distances of all points along the drawn stroke

        p1 = point_list[0]
        length = 0.0

        for i in range(1, len(point_list)):
            length += self.distance(p1, point_list[i])
            p1 = point_list[i]

        return length

    # processes the gesture for normalize size and other things
    def resample(self, points):
        # resample the given stroke's list of points
        # represent the stroke with the amount of step_count points

        # save here the resampled points
        resampled_points = []

        # the sum of the distances of all points along the originally drawn stroke
        length = self.total_length(points)

        # the distance the resampled points have to each other
        stepsize = length / (self.step_count - 1)

        # current position along the strong in regard of step_size (see below)
        curpos = 0

        # add the first point of the original stroke to the point list
        resampled_points.append(points[0])

        # iterate the stroke's point list
        i = 1
        while i < len(points):
            p1 = points[i - 1]

            # calculate the distance of the current pair of points
            d = self.distance(p1, points[i])

            if curpos + d >= stepsize:
                # once we reach or step over our desired distance, we
                # push our resampled point
                # to the correct position based on our stepsize
                nx = p1[0] + ((stepsize - curpos) / d) * \
                    (points[i][0] - p1[0])
                ny = p1[1] + ((stepsize - curpos) / d) * \
                    (points[i][1] - p1[1])

                # store the new data
                resampled_points.append([nx, ny])
                points.insert(i, [nx, ny])

                # reset curpos
                curpos = 0
            else:
                curpos += d

            i += 1

        return resampled_points

    def centroid(self, points):
        xs, ys = zip(*points)

        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def angle_between(self, point, centroid):
        dx = centroid[0] - point[0]
        dy = centroid[1] - point[1]

        # return the angle in degrees
        return np.math.atan2(dy, dx) * 180 / np.math.pi

    def rotate(self, points, center, angle_degree):
        rotated_points = []

        # represent our angle in radians
        angle_rad = angle_degree * (np.pi / 180)

        # define a 3x3 rotation matrix for clockwise rotation
        rot_matrix = np.matrix([[np.cos(angle_rad), -np.sin(angle_rad), 0],
                                [np.sin(angle_rad),  np.cos(angle_rad), 0],
                                [0,               0,        1]])

        t1 = np.matrix([[1, 0, -center[0]],
                        [0, 1, -center[1]],
                        [0, 0,     1]])

        t2 = np.matrix([[1, 0,  center[0]],
                        [0, 1,  center[1]],
                        [0, 0,     1]])

        # create our actual transformation matrix which rotates a
        # point of points around the center of points
        # beware of the order of multiplications, not commutative!
        transform = t2  @ rot_matrix @ t1

        for point in points:

            # homogenous point of the point to be rotated
            hom_point = np.matrix([[point[0]], [point[1]], [1]])

            # rotated point
            rotated_point = transform @ hom_point

            # storing
            rotated_points.append(
                ((rotated_point[0] / rotated_point[2]), float(rotated_point[1] / rotated_point[2])))

        return rotated_points

    def scale(self, points):

        # the desired interval size
        size = 100

        xs, ys = zip(*points)

        # minimum and maximum occurrences of x and y values of the points
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # calculate the range of the coordinates of the points
        x_range = x_max - x_min
        y_range = y_max - y_min

        scaled_points = []

        # map the points to the desired interval
        for p in points:
            p_new = ((p[0] - x_min) * size / x_range,
                     (p[1] - y_min) * size / y_range)
            scaled_points.append(p_new)

        return scaled_points


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    win = IttGestureRecognizer()

    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        sys.exit(app.exec_())

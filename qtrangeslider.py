#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 18:07:35 2022

@author: drIDK, hegedues

the orignal range slider was updated such the it could mimic a simple slider (only a single handle)
without highlighting any range


Imlement label next to slider handle
https://forum.qt.io/topic/44417/placing-a-label-next-to-a-slider-handle

"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys

# custom signal for position tuple
class Values(QObject):
    valuesChanged = pyqtSignal(tuple)


class RangeSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTracking(True)
        self.first_position = 1
        self.second_position = 8
        self.opt = QStyleOptionSlider()
        self.opt.minimum = 0
        self.opt.maximum = 10
        self.setTickPosition(QSlider.TicksAbove)
        self.setTickInterval(1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Fixed,
                                       QSizePolicy.Slider))
        self.signals = Values()
        self.useRange = True

    def setRangeLimit(self, minimum: int, maximum: int):
        self.opt.minimum = minimum
        self.opt.maximum = maximum
        self.update()

    def setRange(self, start: int, end: int):
        self.first_position = start
        self.second_position = end
        self.update()

    def getRange(self):
        return (self.first_position, self.second_position)

    def setTickPosition(self, position: QSlider.TickPosition):
        self.opt.tickPosition = position

    def setTickInterval(self, ti: int):
        self.opt.tickInterval = ti

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        # Draw rule
        self.opt.initFrom(self)
        self.opt.rect = self.rect()
        self.opt.sliderPosition = 0
        self.opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderTickmarks
        #   Draw GROOVE
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)
        #  Draw INTERVAL
        if self.useRange:
            color = self.palette().color(QPalette.Highlight)
            color.setAlpha(160)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            self.opt.sliderPosition = self.first_position
            x_left_handle = (self.style()
                .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
                .right())
            self.opt.sliderPosition = self.second_position
            x_right_handle = (self.style()
                .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
                .left())
            groove_rect = self.style().subControlRect(
                QStyle.CC_Slider, self.opt, QStyle.SC_SliderGroove)
            self.selection = QRect(  # this went into the global namespace so that later it may be grabbed
                x_left_handle,
                groove_rect.y(),
                x_right_handle - x_left_handle,
                groove_rect.height(),
            ).adjusted(-1, 1, 1, -1)
            painter.drawRect(self.selection)
        # Draw first handle
        self.opt.subControls = QStyle.SC_SliderHandle
        self.opt.sliderPosition = self.first_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)
        # Draw second handle
        if self.useRange:
            self.opt.sliderPosition = self.second_position
            self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

    def mousePressEvent(self, event: QMouseEvent):
        self.opt.sliderPosition = self.first_position
        self._first_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self)
        self.opt.sliderPosition = self.second_position
        self._second_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self)

    def mouseMoveEvent(self, event: QMouseEvent):
        distance = self.opt.maximum - self.opt.minimum
        pos = self.style().sliderValueFromPosition(
            0, distance, event.pos().x(), self.rect().width())
        if self._first_sc == QStyle.SC_SliderHandle:
            if pos <= self.second_position:
                self.first_position = pos
                self.update()
                # emit custom signal with position tuple
                self.signals.valuesChanged.emit((self.first_position, self.second_position))
                if self.useRange:
                    return
        if self._second_sc == QStyle.SC_SliderHandle:
            if pos >= self.first_position:
                self.second_position = pos
                self.update()
                # emit custom signal with position tuple
                self.signals.valuesChanged.emit((self.first_position, self.second_position))

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5
        w = SliderLength
        h = self.style().pixelMetric(QStyle.PM_SliderThickness, self.opt, self)
        if (self.opt.tickPosition & QSlider.TicksAbove or self.opt.tickPosition & QSlider.TicksBelow):
            h += TickSpace
        return (self.style()
            .sizeFromContents(QStyle.CT_Slider, self.opt, QSize(w, h), self)
            .expandedTo(QApplication.globalStrut()))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RangeSlider()
    w.show()
    #q = QSlider()
    #q.show()
    app.exec_()
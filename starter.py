#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 10:55:33 2021

@author: zoltan
"""

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QPushButton
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import numpy as np

DIM = (1000, 1000)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        uic.loadUi('future.ui', self)
        self.currentImage = 0
        self.autoColorscale = True
        self.plot()




    def plot(self):
        self.showData = np.random.rand(50, DIM[0], DIM[1])
        for i,im in enumerate(self.showData):
            self.showData[i] = im + i
        self.dark = np.ones(DIM)
        self.white = np.ones(DIM)
        self.white[300:700,300:700] = 2

        self.glw = self.GrphicsLayoutWidget
        self.glw.setBackground('k')
        self.plotItem = self.glw.addPlot(row=0, colspan=2)
        self.plotItem.getViewBox().setAspectLocked(True)
        self.checkBox_fixAspect.setChecked(True)
        self.img = pg.ImageItem()
        self.plotItem.addItem(self.img)
        self.img.setImage(self.showData[self.currentImage], autoLevels=self.autoColorscale)
        #self.gridLayout.addWidget(plot, 0, 1)

        self.img.show()
        self.checkBox_fixAspect.stateChanged.connect(self.fixingAspect)

        self.actionLight_Background.changed.connect(self.toggleBg)

        self.checkBox_autoColor.setChecked(self.autoColorscale)
        self.checkBox_autoColor.stateChanged.connect(self.autoColorscaleSetter)


        self.hist = pg.HistogramLUTItem(image=self.img)
        self.glw.addItem(self.hist, row=0, col=2)
        #self.hist.sigLevelsChanged.connect(self.noAutoColor) # can not really work, see note at the function
        #self.hist.sigLevelChangeFinished.connect(self.noAutoColor) # this is also okay, but looks lazy

        # BACKGROUND
        self.checkBox_subtract.stateChanged.connect(self.backgroundCorrection)
        self.checkBox_divide.stateChanged.connect(self.backgroundCorrection)

        # RANGE
        self.label_rangeFilter.setEnabled(False)
        self.comboBox_filter.setEnabled(False)
        self.label_rangeStart.setText('Image no')
        self.label_rangeFinish.hide()
        self.spinBox_rangeFinish.setEnabled(False)
        # enable on ticking the box
        self.checkBox_useRange.stateChanged.connect(self.enableRange)

        # range slider
        self.label_slider.setText('%5d' % self.horizontalSlider.value())
        self.horizontalSlider.setMaximum(self.showData.shape[0]-1)
        self.horizontalSlider.valueChanged.connect(self.sliderChanged)

        self.spinBox_rangeStart.editingFinished.connect(self.imNoChanged)



    def fixingAspect(self):
        if self.checkBox_fixAspect.isChecked():
            self.plotItem.getViewBox().setAspectLocked(True)
        else:
            self.plotItem.getViewBox().setAspectLocked(False)
        self.img.show()


    def toggleBg(self):
        if self.actionLight_Background.isChecked():
            self.glw.setBackground('w')
        else:
            self.glw.setBackground('k')

    def autoColorscaleSetter(self):
        if self.checkBox_autoColor.isChecked():
            self.img.setImage(self.showData[self.currentImage], autoLevels=True)
            self.checkBox_autoColor.setChecked(True)
            # this is needed otherwise the sigLevelsChanged signal sets the checkbox
            # state back to False after rescaling the colors
            # now the user sets it to true, the the program scales the colors, emits the
            # sigLevelsChanged signal, which sets the checkbox to False, then this
            # line sets it back to True
        else:
            self.img.setImage(self.showData[self.currentImage], autoLevels=False)
            #self.checkBox.setChecked(False)

    # this can not really function properly, because there is no distinction between
    # the user changing the HistogramLUT levels, or it changes, becuase a new image appears
    def noAutoColor(self):
        if not self.checkBox_autoColor.isChecked():
            self.checkBox_autoColor.setChecked(False)

    def enableRange(self):
        if self.checkBox_useRange.isChecked():
            self.label_rangeFilter.setEnabled(True)
            self.comboBox_filter.setEnabled(True)
            self.label_rangeStart.setText('From')
            self.label_rangeFinish.show()
            self.spinBox_rangeStart.setEnabled(True)

            #self.horizontalSlider.show()
            #self.frame_2.show()
        else:
            self.label_rangeFilter.setEnabled(False)
            self.comboBox_filter.setEnabled(False)
            self.label_rangeStart.setText('Image no')
            self.label_rangeFinish.hide()
            self.spinBox_rangeFinish.setEnabled(False)
            self.spinBox_rangeFinish.setValue(0)
            #self.horizontalSlider.hide()
            #self.frame_2.hide()

    def sliderChanged(self):
        self.spinBox_rangeStart.setValue(self.horizontalSlider.value())
        if self.checkBox_useRange.isChecked():
            self.spinBox_rangeFinish.setValue(self.horizontalSlider.value())
        else:
            self.spinBox_rangeFinish.setValue(0)
        self.label_slider.setText('%5d' % self.horizontalSlider.value())
        self.currentImage = self.horizontalSlider.value()

        if self.checkBox_autoColor.isChecked():
            self.img.setImage(self.showData[self.currentImage])
            self.checkBox_autoColor.setChecked(True)
        else:
            self.img.setImage(self.showData[self.currentImage], autoLevels=False)

    def imNoChanged(self):
        self.horizontalSlider.setValue(self.spinBox_rangeStart.value())

    def backgroundCorrection(self):
        autoscale = self.checkBox_autoColor.isChecked()
        if self.checkBox_subtract.isChecked() and self.checkBox_divide.isChecked():
            try:
                divider = self.white-self.dark
                divider[divider==0] = 0.1
                self.img.setImage((self.showData[self.currentImage]-self.dark) / divider, autoLevels=autoscale)
            except ValueError:
                print('Division with zero!')
        elif self.checkBox_subtract.isChecked() and not self.checkBox_divide.isChecked():
            self.img.setImage((self.showData[self.currentImage]-self.dark), autoLevels=autoscale)
        elif not self.checkBox_subtract.isChecked() and self.checkBox_divide.isChecked():
            self.img.setImage(self.showData[self.currentImage] / self.white, autoLevels=autoscale)
        else:
            self.img.setImage(self.showData[self.currentImage], autoLevels=autoscale)
        self.img.show()

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
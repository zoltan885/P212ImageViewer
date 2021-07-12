#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2021 Hegedues

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QRunnable, Qt, QThreadPool, pyqtSignal, QThread, QObject
from PyQt5.QtWidgets import (
    QMainWindow,
    QLabel,
    QGridLayout,
    QWidget,
    QPushButton,
    QProgressBar,
    )
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys, os
import numpy as np
import psutil, resource, time


from version import *
from settings import baseFolder
from dataClass import dataClass
from aux import MemoryMonitorClass, DataLoadClass, DataGenerateClass


DIM = (500, 500)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        print(copyrightNotice)
        uic.loadUi('future.ui', self)
        self.setWindowTitle('%s %i.%i' % (NAME, VERSION['major'], VERSION['minor']+1))
        self.setWindowIcon(QtGui.QIcon('icon/icon32.png'))

        # GET THE DATA
        self.Data = np.random.rand(50, DIM[0], DIM[1])
        for i,im in enumerate(self.Data):
            self.Data[i] = im + i
        self.currentImage = 0
        self.showData = self.Data[self.currentImage]
        self.dark = np.ones(DIM)
        self.dark[:100,:100] = 2
        self.white = np.ones(DIM)
        self.white[300:700,300:700] = 2

        self.dataDict = {}

        # SETTINGS
        self.autoColorscale = True


        self.PID = os.getpid()
        self.prepare()




    def prepare(self):


        self.glw = self.GrphicsLayoutWidget
        self.glw.setBackground('k')
        self.plotItem = self.glw.addPlot(row=0, colspan=2)
        self.plotItem.getViewBox().setAspectLocked(True)
        self.checkBox_fixAspect.setChecked(True)
        self.img = pg.ImageItem()
        self.plotItem.addItem(self.img)
        self.img.setImage(self.showData, autoLevels=self.autoColorscale)
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
        self.checkBox_subtract.stateChanged.connect(self.updateImage)
        self.checkBox_divide.stateChanged.connect(self.updateImage)

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
        self.horizontalSlider.setMaximum(self.Data.shape[0]-1)
        self.horizontalSlider.valueChanged.connect(self.sliderChanged)
        self.horizontalSlider.valueChanged.connect(self.updateImage)


        self.spinBox_rangeStart.editingFinished.connect(self.imNoChanged)


        # TOOLBOX
        self.actionVisible_Image_Manipulation.setChecked(True)
        self.frame.show()
        self.actionVisible_Image_Manipulation.changed.connect(self.visibleImageToolbar)


        # LABELS
        self.labelL = self.glw.addLabel(text='', row=5, col=0, colspan=1, justify='right')
        self.labelR = self.glw.addLabel(text='', row=5, col=1, colspan=1, justify='right')
        self.labelL.setText('')
        self.labelR.setText('')
        # IMAGE HOVER
        self.img.hoverEvent = self.imageHoverEvent


        # STATUS BAR SETTINGS

        self.statusBar().showMessage('Loaded %d images' % self.Data.shape[0])
        self.statusUsageLabel = QLabel()
        self.statusBar().addPermanentWidget(self.statusUsageLabel)



        # SETUP MEMORY AND CPU USAGE IN THE STATUS BAR
        self.memthread = QThread()
        self.memoryMonitor = MemoryMonitorClass()
        self.memoryMonitor.moveToThread(self.memthread)
        self.memoryMonitor.memorySignal.connect(self.reportMemory)

        self.memthread.started.connect(self.memoryMonitor.run)
        self.memthread.start()

        # Load in different thread & progressBar
        self.actionLoad_Image.triggered.connect(self.load)


        # Load ThreadPool & progressBar
        self.actionLoad_Folder.triggered.connect(self.loadThreadPool)

    def loadThreadPool(self):
        '''
        test function to load data with QThreadPool
        '''
        self.threadpool = QThreadPool()
        dataGenerate = DataGenerateClass(size=100)
        dataGenerate.signals.started.connect(self.addProgressBar)
        dataGenerate.signals.result.connect(self.updateThreadData)
        dataGenerate.signals.progress.connect(self.updateProgressBar)
        dataGenerate.signals.finished.connect(self.removeProgressBar)
        self.threadpool.start(dataGenerate)


    def updateThreadData(self, data):
        name = 'name'  # this is the name of the dataset
        if name not in self.dataDict.keys():
            self.dataDict[name] = data
        else:
            self.dataDict[name] = np.concatenate((self.dataDict[name], data))

    def load(self):
        '''
        test function to load data with separate thread
        '''
        self.loadThread = QThread()
        self.loading = DataLoadClass()
        self.loading.moveToThread(self.loadThread)
        self.loading.dataLoadSignal.connect(self.updateProgressBar)
        self.loading.dataLoadStartSignal.connect(self.addProgressBar)
        self.loading.dataLoadFinishedSignal.connect(self.removeProgressBar)
        # destroy thread at the end of loading!
        self.loading.dataLoadFinishedSignal.connect(self.loadThread.quit)
        self.loading.dataLoadFinishedSignal.connect(self.loading.deleteLater)
        self.loading.dataLoadFinishedSignal.connect(self.loadThread.deleteLater)

        self.loadThread.started.connect(self.loading.run)
        self.loadThread.start()



    def addProgressBar(self):
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.statusBar().insertPermanentWidget(0, self.progressBar)

    def removeProgressBar(self):
        self.statusBar().removeWidget(self.progressBar)

    def updateProgressBar(self, progress):
        self.progressBar.setValue(progress)



    def imageHoverEvent(self, event):
        '''Show the position, pixel, and value under the mouse cursor.'''
        if event.isExit():
            self.labelL.setText('')
            self.labelR.setText('')
            return
        pos = event.pos()
        i, j = pos.x(), pos.y()
        i = int(np.clip(i, 0, self.showData.shape[0] - 1))
        j = int(np.clip(j, 0, self.showData.shape[1] - 1))
        val = self.showData[i, j]
        self.labelR.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), val))



    def visibleImageToolbar(self):
        if self.actionVisible_Image_Manipulation.isChecked():
            self.frame.show()
        else:
            self.frame.hide()

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
            self.img.setImage(self.showData, autoLevels=True)
            self.checkBox_autoColor.setChecked(True)
            # this is needed otherwise the sigLevelsChanged signal sets the checkbox
            # state back to False after rescaling the colors
            # now the user sets it to true, the the program scales the colors, emits the
            # sigLevelsChanged signal, which sets the checkbox to False, then this
            # line sets it back to True
        else:
            self.img.setImage(self.showData, autoLevels=False)
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

            # self.horizontalSlider.show()
            # self.frame_2.show()
        else:
            self.label_rangeFilter.setEnabled(False)
            self.comboBox_filter.setEnabled(False)
            self.label_rangeStart.setText('Image no')
            self.label_rangeFinish.hide()
            self.spinBox_rangeFinish.setEnabled(False)
            self.spinBox_rangeFinish.setValue(0)
            # self.horizontalSlider.hide()
            # self.frame_2.hide()

    def sliderChanged(self):
        self.spinBox_rangeStart.setValue(self.horizontalSlider.value())
        if self.checkBox_useRange.isChecked():
            self.spinBox_rangeFinish.setValue(self.horizontalSlider.value())
        else:
            self.spinBox_rangeFinish.setValue(0)
        self.label_slider.setText('%5d' % self.horizontalSlider.value())
        # self.currentImage = self.horizontalSlider.value()
        # self.showData = self.Data[self.currentImage]

    def getCurrentImage(self):
        '''
        gets the current image or current image range (if range it returns a slice instance)
        '''
        #self.currentImage = self.horizontalSlider.value()
        return self.horizontalSlider.value()
        #self.showData = self.Data[self.currentImage]

    def imNoChanged(self):
        self.horizontalSlider.setValue(self.spinBox_rangeStart.value())
        # automatically calls self.sliderChanged

    def backgroundCorrection(self):
        if self.checkBox_subtract.isChecked() and self.checkBox_divide.isChecked():
            try:
                divider = self.white-self.dark
                divider[divider == 0] = 0.1
                self.showData = (self.showData-self.dark) / divider
            except ValueError:
                print('Division with zero!')
        elif self.checkBox_subtract.isChecked() and not self.checkBox_divide.isChecked():
            self.showData = self.showData-self.dark
        elif not self.checkBox_subtract.isChecked() and self.checkBox_divide.isChecked():
            self.showData = self.showData / self.white
        else:
            pass

    def filterImages(self, ims):
        '''
        max or average filtering of an image range 
        so far it is done in the self.updateRegion function
        ims is the array of images to filter
        '''
        if self.currentFilter == 'average':
            self.showData = np.mean(ims, axis=0)
        elif self.currentFilter == 'max':
            self.showData = np.maximum.reduce(ims, axis=0)



    def updateImage(self):
        autoscale = self.checkBox_autoColor.isChecked()
        self.showData = self.Data[self.getCurrentImage()]

        #self.getCurrentImage()
        self.backgroundCorrection()
        self.img.setImage(self.showData, autoLevels=autoscale)
        self.img.show()

    def reportMemory(self, memoryThis, memoryPerc, cpuPerc):
        #self.statusBar().showMessage('PID: %s; %.1f MB; free mem: %.1f%%;  cpu %.1f' % (self.PID, memoryThis, 100-memoryPerc, cpuPerc))
        mem = memoryThis
        memunit='MB'
        if memoryThis > 1000:
            mem = memoryThis/1000.
            memunit = 'GB'
        self.statusUsageLabel.setText('PID: %s; %.1f %s; free mem: %.1f%%;  cpu %.1f' %
                                      (self.PID, mem, memunit, 100-memoryPerc, cpuPerc))






def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

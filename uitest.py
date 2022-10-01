#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 19:20:34 2022

@author: hegedues
"""

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtWidgets import QLabel, QProgressBar
from PyQt5.QtGui import QTransform

#from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys, os
import numpy as np
import time
#import psutil, resource, time


from version import NAME, VERSION, copyrightNotice
from settings import baseFolder
#from dataClass import dataClass
from aux import MemoryMonitorClass, ImageData
from plotarea import plotArea
from tabcontent import tabContent



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(copyrightNotice)
        uic.loadUi('future4.ui', self)
        self.setWindowTitle('%s %i.%i' % (NAME, VERSION['major'], VERSION['minor']+1))
        self._addStatusBar()



    def _addStatusBar(self):
        # STATUS BAR SETTINGS
        self.statusUsageLabel = QLabel()
        self.statusBar().addPermanentWidget(self.statusUsageLabel)
        # SETUP MEMORY AND CPU USAGE IN THE STATUS BAR
        self.memthread = QThread()
        self.memoryMonitor = MemoryMonitorClass()
        self.memoryMonitor.moveToThread(self.memthread)
        self.memthread.started.connect(self.memoryMonitor.run)
        self.memoryMonitor.usageSignal.connect(self.showUsage)
        self.memthread.start()

    def showUsage(self, label):
        self.statusUsageLabel.setText(label)


    # This is a quick testing function
    def keyPressEvent(self, event):
        w = self.tabWidget.currentWidget()
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_P:   # test progress bar
                print('Ctrl pressed')
                self.testProgressBar()
            elif event.key() == Qt.Key_N:  # new tab
                name = 'tab_%d' % self.tabWidget.nextTabIdx
                self.tabWidget._addTab(name)
            elif event.key() == Qt.Key_Z:  # show/hide ImageToolbar in current tab
                print('toggling ImageToolbar visbility for tab: %d' % self.tabWidget.currentIndex())
                w.showImageToolbar()
            elif event.key() == Qt.Key_A:
                print('Enable ImageToolbar')
                w._enableUponDataPresent()
            elif event.key() == Qt.Key_D:
                print('Disable ImageToolbar')
                w._disableAll()


    def testProgressBar(self):
        t0 = time.time()
        self.addProgressBar()
        dt = 3.
        while time.time() - t0 < dt:
            self.updateProgressBar(int((time.time() - t0)/dt*100))
        self.updateProgressBar(100)
        time.sleep(1)
        self.removeProgressBar()


    def addProgressBar(self):
        print('Adding progress bar')
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.statusBar().insertPermanentWidget(0, self.progressBar)

    def removeProgressBar(self):
        self.statusBar().removeWidget(self.progressBar)

    def updateProgressBar(self, progress):
        self.progressBar.setValue(progress)






def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 19:20:34 2022

@author: hegedues
"""

'''
Advanced docking:
    https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System
    https://github.com/KDAB/KDDockWidgets
'''



from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtWidgets import QLabel, QProgressBar


#from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys, os
import numpy as np
import time
import argparse
#import psutil, resource, time


from version import NAME, VERSION, copyrightNotice
from settings import baseFolder
#from dataClass import dataClass
from aux import MemoryMonitorClass

from plotarea import plotArea
from tabcontent import tabContent



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(copyrightNotice)
        uic.loadUi('future4.ui', self)
        self.setWindowTitle('%s %i.%i' % (NAME, VERSION['major'], VERSION['minor']+1))
        self._addStatusBar()
        self._addMenu()

        self._addSignals()

        self.data = []



    def _addMenu(self):
        self.actionQuit.triggered.connect(self.leaveProgram)
        #self.actionLoad_Dummy.triggered.connect(self.generateWithClass)



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

    def _addSignals(self):
        sigs = self.tabWidget.currentWidget().plotArea.data.generator
        sigs.started.connect(self._signalTester)
        sigs.started.connect(self._addProgressBar)
        sigs.progress.connect(self._updateProgressBar)
        sigs.finished.connect(self._removeProgressBar)


    def showUsage(self, label):
        self.statusUsageLabel.setText(label)



    # This is for quick functionality testing
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
            elif event.key() == Qt.Key_W:
                print('\'OPEN\'')
                w.plotArea._generateImgData('d')
            elif event.key() == Qt.Key_T:
                w.plotArea._transform()


    def _signalTester(self):
        print('I got a signal')

    def testProgressBar(self):
        t0 = time.time()
        self._addProgressBar()
        dt = 3.
        while time.time() - t0 < dt:
            self._updateProgressBar(int((time.time() - t0)/dt*100))
        self._updateProgressBar(100)
        time.sleep(1)
        self._removeProgressBar()


    def _addProgressBar(self):
        print('Adding progress bar')
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.statusBar().insertPermanentWidget(0, self.progressBar)

    def _removeProgressBar(self):
        self.statusBar().removeWidget(self.progressBar)

    def _updateProgressBar(self, progress):
        self.progressBar.setValue(progress)




    def leaveProgram(self):
        print('bye')
        sys.exit()





def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

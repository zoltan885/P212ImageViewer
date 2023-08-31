#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  2 10:42:31 2022

@author: hegedues
"""

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread, Qt, QRect
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



class ConstantXROI(pg.ROI):
    constant_x = 0

    def setPos(self, pos, y=None, update=True, finish=True):
        pos.setX(self.constant_x)
        super().setPos(pos, y=y, update=update, finish=finish)


DOTSIZE = 4

IMAGE1 = np.random.random(size=(200,200))
IMAGE2 = np.random.random(size=(200,200))

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(copyrightNotice)
        uic.loadUi('follow_pointer.ui', self)

        # setup left image
        self.leftImg.setBackground('k')
        self.plotItemL = self.leftImg.addPlot(row=0, colspan=2)
        #self.plotItemL.getViewBox().register('name1')   # this would add this view box to the list so that all others
                                                        # could link axes with this one, but linking does not seem to
                                                        # work really work
        self.plotItemL.getViewBox().setAspectLocked(True)
        self.imgL = pg.ImageItem()
        self.plotItemL.addItem(self.imgL)
        self.imgL.setImage(IMAGE1, autoLevels=True)
        self.imgL.show()
        self.labelL = self.leftImg.addLabel(text='', row=1, col=0, colspan=1, justify='right')
        self.imgL.hoverEvent = self.imageLHoverEvent

        # setup right image
        self.rightImg.setBackground('k')
        self.plotItemR = self.rightImg.addPlot(row=0, colspan=2)
        self.plotItemR.getViewBox().setAspectLocked(True)
        self.imgR = pg.ImageItem()
        self.plotItemR.addItem(self.imgR)
        self.imgR.setImage(IMAGE2, autoLevels=True)
        self.imgR.show()
        self.labelR = self.rightImg.addLabel(text='', row=1, col=0, colspan=1, justify='right')
        self.imgR.hoverEvent = self.imageRHoverEvent

        # link the viewBoxes
#        self.plotItemR.getViewBox().linkView(self.plotItemR.getViewBox().XAxis, self.plotItemL.getViewBox())
#        self.plotItemR.getViewBox().linkView(self.plotItemR.getViewBox().YAxis, self.plotItemL.getViewBox())
#        self.plotItemL.getViewBox().linkView(self.plotItemL.getViewBox().XAxis, self.plotItemR.getViewBox())
#        self.plotItemL.getViewBox().linkView(self.plotItemL.getViewBox().YAxis, self.plotItemR.getViewBox())
        # unlink
        # self.plotItemR.getViewBox().linkView(self.plotItemR.getViewBox().XAxis, None)
        # self.plotItemR.getViewBox().linkView(self.plotItemR.getViewBox().YAxis, None)
        # self.plotItemL.getViewBox().linkView(self.plotItemL.getViewBox().XAxis, None)
        # self.plotItemL.getViewBox().linkView(self.plotItemL.getViewBox().YAxis, None)

        self.dot = pg.CircleROI((0, 0), size=(DOTSIZE, DOTSIZE), pen={'color': "FF0000", 'width': 7})
        self.hline = pg.InfiniteLine((0), angle=0, pen={'color': "FF0000", 'width': 3})
        self.vline = pg.InfiniteLine((0), angle=90)
        
        self.roi = ConstantXROI((0, 0), (200,1), pen='r', translateSnap=True, resizable=False)
        self.roi.addTranslateHandle((0.5, 1))
        self.plotItemR.addItem(self.roi)
        self.roi.removeHandle(0)

        # setup histogram
        self.hist = pg.HistogramLUTItem(image=self.imgL)
        self.colorscale.addItem(self.hist, row=0, col=0)
        # define phantom histogram for the second image, that will just mimic the first histogram
        self.phantomHist = pg.HistogramLUTItem(image=self.imgR)
        self.hist.sigLevelsChanged.connect(self._updatePhantomHistLevels)
        self.hist.sigLookupTableChanged.connect(self._updatePhantomHistLookupTable)

    def _updatePhantomHistLevels(self):
        mi,ma = self.hist.getLevels()
        self.phantomHist.setLevels(min=mi, max=ma)

    def _updatePhantomHistLookupTable(self):
        self.imgR.setLookupTable(self.hist.getLookupTable(img=IMAGE1))

    def imageLHoverEvent(self, event):
        '''Show the position, pixel, and value under the mouse cursor.'''
        if event.isExit():
            self.labelL.setText('')
            self.labelR.setText('')
            self.plotItemR.removeItem(self.dot)
            self.plotItemR.removeItem(self.hline)
            self.plotItemR.removeItem(self.vline)
            
            return
        pos = event.pos()
        i, j = pos.x(), pos.y()
        i = int(np.clip(i, 0, IMAGE1.shape[0] - 1))
        j = int(np.clip(j, 0, IMAGE1.shape[1] - 1))
        valL = IMAGE1[j, i]
        valR = IMAGE2[j, i]
        self.labelL.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), valL))
        self.labelR.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), valR))
        self.plotItemR.addItem(self.dot)
        self.dot.maxBounds = QtCore.QRect(2*DOTSIZE, 2*DOTSIZE, 200-2*DOTSIZE, 200-2*DOTSIZE)
        self.dot.setPos((i-DOTSIZE/2+0.5, j-DOTSIZE/2+0.5))
        
        self.plotItemR.addItem(self.hline)
        self.hline.setValue(j)
        self.plotItemR.addItem(self.vline)
        self.vline.setValue(i)
        


    def imageRHoverEvent(self, event):
        '''Show the position, pixel, and value under the mouse cursor.'''
        if event.isExit():
            self.labelL.setText('')
            self.labelR.setText('')
            self.plotItemL.removeItem(self.dot)
            return
        pos = event.pos()
        i, j = pos.x(), pos.y()
        i = int(np.clip(i, 0, IMAGE1.shape[0] - 1))
        j = int(np.clip(j, 0, IMAGE1.shape[1] - 1))
        valL = IMAGE1[j, i]
        valR = IMAGE2[j, i]
        self.labelL.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), valL))
        self.labelR.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), valR))
        self.plotItemL.addItem(self.dot)
        self.dot.maxBounds = QtCore.QRect(2*DOTSIZE, 2*DOTSIZE, 200-2*DOTSIZE, 200-2*DOTSIZE)
        self.dot.setPos((i-DOTSIZE/2+0.5, j-DOTSIZE/2+0.5))







def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

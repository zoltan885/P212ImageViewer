#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  1 10:12:31 2022

@author: hegedues
"""
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QTransform

import pyqtgraph as pg
import numpy as np

from aux2 import dataSet



IMAGE1 = np.random.random(size=(200,200))
IMAGE2 = np.random.random(size=(200,200))
DOTSIZE = 4


class plotArea(QtWidgets.QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent)  # this is needed for the promotion
        uic.loadUi('plotAreaWidget2.ui', self)
        print('Plot area created')

        self.data = dataSet()
        self.tr = QTransform()

        self.plot2DWidget.setBackground('k')
        self.plot2d = self.plot2DWidget.addPlot(row=0, colspan=2)
        self.plot2d.getViewBox().setAspectLocked(True)
        self.img2d = pg.ImageItem()
        self.plot2d.addItem(self.img2d)
        self.img2d.setImage(IMAGE1, autoLevels=True)
        self.img2d.show()
        self.labelL = self.plot2DWidget.addLabel(text='', row=1, col=0, colspan=1, justify='right')
        self.img2d.hoverEvent = self.imageLHoverEvent
        #self._setAxisLabel()

        # hide 1D plot
        self.plot1DWidget.hide()

        # setup histogram
        self.hist = pg.HistogramLUTItem(image=self.img2d)
        self.plotHistoWidget.addItem(self.hist, row=0, col=0)



    def _toggle1dVisibility(self):
        pass

    def _generateImgData(self, plotdata, autolevels=True):
        #self.img2d.setImage(plotdata, autLevels = autolevels)
        self.data.generator.finished.connect(self._updateImage)
        self.data.generate()

    def _updateImage(self):
        self.img2d.setImage(self.data.plotData, autLevels = True)

    def imageLHoverEvent(self, event):
        '''Show the position, pixel, and value under the mouse cursor.'''
        if event.isExit():
            self.labelL.setText('')
            #self.labelR.setText('')
            #self.plotItemR.removeItem(self.dot)
            return
        pos = event.pos()
        currentImage = self.img2d.image
        i, j = pos.x(), pos.y()
        i = int(np.clip(i, 0, currentImage.shape[0] - 1))
        j = int(np.clip(j, 0, currentImage.shape[1] - 1))
        valL = self.img2d.image[i, j]
        #valR = IMAGE2[j, i]
        self.labelL.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), valL)) #size='12pt'
        #self.labelR.setText("pixel: (%4d, %4d), value: %.3f" % (pos.x(), pos.y(), valR))
        #self.plotItemR.addItem(self.dot)
        #self.dot.maxBounds = QtCore.QRect(2*DOTSIZE, 2*DOTSIZE, 200-2*DOTSIZE, 200-2*DOTSIZE)
        #self.dot.setPos((i-DOTSIZE/2+0.5, j-DOTSIZE/2+0.5))

    def _transform(self):
        print('Transforming')
        self.tr.scale(0.00015, 0.00015)  # set detector pixel size -> convert to physical length instead of pix
        self.tr.translate(0, 0)  # move the image; perhaps good for multi detector view
        self.img2d.setTransform(self.tr)
        self._setAxisLabel(unit='m')

    def _setAxisLabel(self, show=True, unit='pix'):
        self.plot2d.setLabel('bottom', "", units=unit)
        self.plot2d.setLabel('left', "", units=unit)










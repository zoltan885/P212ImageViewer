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


import sys, os
import glob
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QCheckBox, QProgressBar, QMessageBox, QDialog
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QPushButton
from PyQt5.QtCore import QSize, Qt
from scipy import interpolate, stats
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import matplotlib.pyplot as plt
import numpy as np
import fabio
import psutil
import scipy.ndimage
#from numba import jit
import time


from version import *
from settings import baseFolder
from dataClass import dataClass





class Data():
    def __init__(self, *args):
        self.defaultData = np.ones((500,500))




class CBF(QWidget):
    def __init__(self, *args):
        super().__init__()
        print(copyrightNotice)
        self.title = '%s %i.%i.%i' % (NAME, VERSION['major'], VERSION['minor'], VERSION['patch'])
        self.Images = []  # np.zeros((1,100, 100))
        # self.showData = self.Images[0]
        # self.ImageData = self.Images[0]
        self.currentImage = 0
        self.currentFilter = 'average'
        self.autoColorscale = True
        self.knownFileTypes = ['tif', 'cbf']

        self.LinePlotActive = False
        self.roiColors = ("FF0000", (2, 9), (5, 9), (7, 9))  # for several ROIs eventually
        self.ROIs = []  # visualization
        self.ROIArea = []  # area used to calculate
        self.ROICurves = []  # 1D curve
        self.lineCuts = []
        self.lineCutsArea = []
        self.lineCutsCurves = []

        pg.setConfigOptions(imageAxisOrder='row-major')
        self.initUI()
        #if len(args[0]) > 1:
        #    if args[0][1] == '-D':
        #        DEB = True
        #if DEB:
        #    self.loadFolder(folder='/home/zoltan/Documents/code_snippets/multisource/1')

    def _checkSize(self, filelist, maxOccupation=0.8):
        size = np.sum([os.path.getsize(f) for f in filelist])
        if size > maxOccupation * psutil.virtual_memory().available:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle("Error")
            msgBox.setText("%.1f %% of available memory (%.1f GB) exceeded!" %
                           (100*maxOccupation, float(psutil.virtual_memory().available)/1024**3))
            msgBox.exec()
            return False
        return True


    def updateProgressBar(self, r):
        self.progressBar.setValue(int(100*r))


    def loadDataFolder(self):
        d = dataClass()
        path = QFileDialog.getExistingDirectory(self, "Select a folder to load", baseFolder, QFileDialog.ShowDirsOnly)
        self.progressBar.setMaximum(100)  # this has to be a larger integer
        self.progressBar.show()
        slicing = self.p.param('Actions', 'Slicing').value()
        d.loadFolder(path=path, slicing=slicing, callback=self.updateProgressBar)
        self.progressBar.hide()
        self.statusLabel.setText('%d images loaded' % d.data.shape[0])
        self.ImageData = d.data
        self.Images = d.files
        self.steps = d.steps
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds((0, len(self.Images)))
        self.updateRegion()

    def loadEiger2(self):
        d = dataClass()
        fname = QFileDialog.getOpenFileNames(self, "Open file", baseFolder, "Image Files (*.cbf *.tif *.h5 *nexus)")[0][0]
        self.progressBar.setMaximum(100)  # this has to be a larger integer
        self.progressBar.show()
        slicing = self.p.param('Actions', 'Slicing').value()
        d.loadEiger2(fname=fname, slicing=slicing, callback=self.updateProgressBar)
        self.progressBar.hide()
        self.ImageData = d.data
        self.Images = d.files
        self.steps = d.steps
        self.imageRegion.setRegion((0, 1))
        #print(self.Images)
        #print(self.imageRegion.bounds)
        self.imageRegion.setBounds((0, len(self.Images)))
        self.updateRegion()


    def loadDataFile(self):
        d = dataClass()
        path = QFileDialog.getOpenFileNames(self, "Open file", baseFolder, "Image Files (*.cbf *.tif *.h5 *nexus)")[0][0]
        d.loadFile(path=path)
        self.ImageData = d.data
        self.Images = d.files
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds((0, 1))
        self.updateRegion()


    '''
    def subtractDark(self):
        if self.p.param('Data Processing', 'subtract_dark').value():
            if self.Dark is not None:
                self.ImageData = np.array([im-self.Dark for im in self.ImageData])
                self.updateRegion()
            else:
                pass
    '''

    def initUI(self):
        self.setWindowTitle(self.title)
        # self.setWindowIcon(QtWidgets.QSystemTrayIcon('test_icon.png'))
        gridLayout = QGridLayout(self)
        self.setLayout(gridLayout)

        params = [
            {'name': 'Actions', 'type': 'group', 'children': [
                {'name': 'LoadDataFolder', 'type': 'action'},
                {'name': 'LoadDataFile', 'type': 'action'},
                {'name': 'Load Eiger2', 'type': 'action'},
                #{'name': 'Load Image', 'type': 'action'},
                #{'name': 'Load Folder', 'type': 'action'},
                #{'name': 'Load Folder Mem', 'type': 'action'},
                #{'name': 'Load Folder WD', 'type': 'action'},
                #{'name': 'Load Folder tif', 'type': 'action'},
                {'name': 'Slicing', 'type': 'str', 'value': '0:None:1', 'step': 1},
                # {'name': 'Dark Image', 'type': 'action'},
                # {'name': 'Mask Image', 'type': 'action'},
            ]},
            {'name': 'Data Processing', 'type': 'group', 'children': [
                {'name': 'imageNo', 'type': 'int', 'value': 0, 'step': 1, 'bounds': (0, 0)},
                {'name': 'iOrient', 'type': 'list', 'values': ['none', 'flipUD', 'flipLR', 'transpose', 'rot90', 'rot180', 'rot270', 'rot180 + tr']},
                {'name': 'maskValsAbove', 'type': 'float', 'value': 0, 'step': 100.},

                {'name': 'rangeFilter', 'type': 'list', 'values': ['average', 'max']},
                {'name': 'autoColorscale', 'type': 'bool', 'value': self.autoColorscale},
                {'name': 'Line plots', 'type': 'list', 'values': ['', 'line cut', 'ROI']},
                {'name': 'nROI', 'type': 'int', 'value': 1, 'step': 1, 'bounds': (1, 4), 'visible': False},
                # {'name': 'subtract_dark', 'type': 'bool', 'value': False},
            ]},
            {'name': 'Iso Line', 'type': 'group', 'children': [
                {'name': 'show', 'type': 'bool', 'value': False},
                {'name': 'iso', 'type': 'float', 'value': 0, 'step': 0.1},
            ]},
            {'name': 'Appearence', 'type': 'group', 'children': [
                {'name': 'light_bg', 'type': 'bool', 'value': False},
            ]}
        ]

        def toggleBg():
            if self.p.param('Appearence', 'light_bg').value():
                self.win.setBackground('w')
            else:
                self.win.setBackground('k')

        def subtractDark():
            self.subtractDark()

        self.p = Parameter.create(name='params', type='group', children=params)
        self.p.param('Actions', 'LoadDataFolder').sigActivated.connect(self.loadDataFolder)
        self.p.param('Actions', 'LoadDataFile').sigActivated.connect(self.loadDataFile)
        self.p.param('Actions', 'Load Eiger2').sigActivated.connect(self.loadEiger2)
        #self.p.param('Actions', 'Load Image').sigActivated.connect(self.loadImage)
        #self.p.param('Actions', 'Load Folder').sigActivated.connect(self.loadFolder)
        #self.p.param('Actions', 'Load Folder Mem').sigActivated.connect(self.loadFolderMapped)
        #self.p.param('Actions', 'Load Folder WD').sigActivated.connect(self.loadFolderWithDark)
        #self.p.param('Actions', 'Load Folder tif').sigActivated.connect(self.loadFolderTif)
        self.p.param('Data Processing', 'imageNo').sigValueChanged.connect(self.changeImageNo)
        #self.p.param('Data Processing', 'iOrient').sigValueChanged.connect(self.updateRegion)
        self.p.param('Data Processing', 'maskValsAbove').sigValueChanged.connect(self.updateRegion)
        self.p.param('Data Processing', 'rangeFilter').sigValueChanged.connect(self.changeFilter)
        self.p.param('Data Processing', 'autoColorscale').sigValueChanged.connect(self.changeAutocolorscale)
        #self.p.param('Data Processing', 'roi').sigValueChanged.connect(self.showROI)
        self.p.param('Data Processing', 'Line plots').sigStateChanged.connect(self.updateTree)
        #self.p.param('Data Processing', 'Line plots').sigStateChanged.connect(self.showROI)
        self.p.param('Data Processing', 'nROI').sigValueChanged.connect(self.showROI)  # sigValueChanged combines fast changes to a single signal
        self.p.param('Appearence', 'light_bg').sigValueChanged.connect(toggleBg)
        # self.p.param('Data Processing', 'subtract_dark').sigValueChanged.connect(subtractDark)
        # self.p.param('Iso Line', 'iso').sigValueChanged.connect(self.updateRegion)
        self.p.param('Iso Line', 'show').sigStateChanged.connect(self.updateTree)
        self.p.param('Iso Line', 'iso').sigValueChanged.connect(self.updateRegion)


        # self.p.param('Data Processing', 'Rotation').sigValueChanging.connect(cAngChange)

        t = ParameterTree()
        t.setMaximumWidth(320)
        t.setParameters(self.p, showTop=False)

        gridLayout.addWidget(t, 0, 1)
        self.win = pg.GraphicsLayoutWidget()
        gridLayout.addWidget(self.win, 0, 2)

        self.progressBar = QProgressBar()
        gridLayout.addWidget(self.progressBar, 1, 1, 1, 2)

        self.statusLabel = QLabel('Status')
        gridLayout.addWidget(self.statusLabel, 1, 1, 1, 2)



        self.win.nextRow()
        self.p2 = self.win.addPlot(row=3, colspan=3)
        self.imageRegion = pg.LinearRegionItem(bounds=[0, None], swapMode='push')
        self.imageRegion.sigRegionChanged.connect(self.updateRegion)

        self.p2.setMaximumHeight(80)
        self.p2.addItem(self.imageRegion)
        self.p2.showAxis('left', show=False)

        self.p3 = self.win.addPlot(row=0, col=0)
        self.imgLeft = pg.ImageItem()
        self.p3.getViewBox().setAspectLocked(True)
        self.p3.addItem(self.imgLeft)
        #self.imgLeft.setLookupTable('fire')

        self.iso = pg.IsocurveItem(level=0.8, pen='g')
        self.iso.setParentItem(self.imgLeft)
        self.iso.setZValue(self.p.param('Iso Line', 'iso').value())
        self.p.param('Iso Line', 'iso').hide()

        #self.p.param('Data Processing', 'nROI').hide()

        # self.p4 = win.addPlot(row=2, col=0)
        # self.p4.hide()


        # self.ctrROI=pg.LineROI([0, 5], [0, 0], width=2, pen=(1,9))

        self.hist = pg.HistogramLUTItem(image=self.imgLeft)
        self.hist.imageItem().setLookupTable('flame')
        #self.hist.setImageItem(self.imgLeft)
        # self.hist.setMaximumWidth(150)
        self.win.addItem(self.hist, row=0, col=2)
        self.imgLeft.hoverEvent = self.imageHoverEvent


        # add bottom labels
        self.LabelL = self.win.addLabel(text='', row=5, col=0, colspan=1, justify='right')
        self.LabelR = self.win.addLabel(text='', row=5, col=1, colspan=2, justify='right')


        self.win.show()
        self.setMinimumSize(1440, 900)
        self.show()

    def imageHoverEvent(self, event):
        '''Show the position, pixel, and value under the mouse cursor.'''
        if event.isExit():
            if self.currentImage[0] == self.currentImage[1]-1:
                # self.p3.setTitle("%s" % self.Images[self.currentImage[0]].rpartition('/')[2])
                self.LabelL.setText("%s" % self.Images[self.currentImage[0]].rpartition('/')[2])
            else:
                # self.p3.setTitle("Mean of images: %i:%i" % (self.currentImage[0]*self.steps, self.currentImage[1]*self.steps))
                self.LabelL.setText("Mean of images: %i:%i" % (self.currentImage[0]*self.steps, self.currentImage[1]*self.steps))
            return
        pos = event.pos()
        i, j = pos.y(), pos.x()
        if len(self.ImageData.shape) == 3:
            i = int(np.clip(i, 0, self.ImageData.shape[1] - 1))
            j = int(np.clip(j, 0, self.ImageData.shape[2] - 1))
        elif len(self.ImageData.shape) == 2:
            i = int(np.clip(i, 0, self.ImageData.shape[0] - 1))
            j = int(np.clip(j, 0, self.ImageData.shape[1] - 1))
        val = self.showData[i, j]
        # self.p3.setTitle("pixel: (%d, %d), value: %.1f" % (i, j, val))
        self.LabelL.setText("pixel: (%d, %d), value: %.1f" % (i, j, val))

    def ROIHoverEvent(self, event):
        if event.isExit():
            self.LabelR.setText('')
        else:
            pos = event.pos()
            mappedPos = self.roiPlot.vb.mapSceneToView(pos)
            x, y = mappedPos.x(), mappedPos.y()
            self.LabelR.setText('%.1f %.1f' % (x, y))

    def prepImages(self):
        '''
        Transform images (works on the whole 3d image stack, where the 1st axis is the image no):
        some source material:
            https://stackoverflow.com/questions/41309201/efficient-transformations-of-3d-numpy-arrays
        '''

        print('prepImages called')
        # first transform the images back to the original state
        if self.trOrient is None:
            pass
        elif self.trOrient == 'flipUD':
            self.ImageData = self.ImageData[:, ::-1, :]
            self.trOrient = None
        elif self.trOrient == 'flipLR':
            self.ImageData = self.ImageData[:, :, ::-1]
            self.trOrient = None
        elif self.trOrient == 'rot90':
            self.ImageData = np.rot90(self.ImageData, k=1, axes=(2, 1))
            self.trOrient = None
        elif self.trOrient == 'rot180':
            self.ImageData = np.rot90(self.ImageData, k=2, axes=(2, 1))
            self.trOrient = None
        elif self.trOrient == 'rot270':
            self.ImageData = np.rot90(self.ImageData, k=3, axes=(2, 1))
            self.trOrient = None
        elif self.trOrient == 'transpose':
            self.ImageData = self.ImageData.transpose(0, 2, 1)
            self.trOrient = None
        elif self.trOrient == 'rot180 + tr':
            self.ImageData = np.rot90(self.ImageData, k=2, axes=(2, 1)).transpose(0, 2, 1)
            self.trOrient = None

        # now transform to the desired state
        if self.p.param('Data Processing', 'iOrient').value() == 'flipUD':
            self.ImageData = self.ImageData[:, ::-1, :]
            self.trOrient = 'flipUD'
        elif self.p.param('Data Processing', 'iOrient').value() == 'flipLR':
            self.ImageData = self.ImageData[:, :, ::-1]
            self.trOrient = 'flipLR'
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot90':
            self.ImageData = np.rot90(self.ImageData, k=1, axes=(1, 2))
            self.trOrient = 'rot90'
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot180':
            self.ImageData = np.rot90(self.ImageData, k=2, axes=(1, 2))
            self.trOrient = 'rot180'
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot270':
            self.ImageData = np.rot90(self.ImageData, k=3, axes=(1, 2))
            self.trOrient = 'rot270'
        elif self.p.param('Data Processing', 'iOrient').value() == 'transpose':
            self.ImageData = self.ImageData.transpose(0, 2, 1)
            self.trOrient = 'transpose'
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot180 + tr':
            self.ImageData = np.rot90(self.ImageData.transpose(0, 2, 1), k=2, axes=(1, 2))
            self.trOrient = 'rot180 + tr'
        self.updateRegion()

    def prepFinalImage(self, img):
        '''
        Transform 2d array
        '''
        if self.p.param('Data Processing', 'iOrient').value() == 'flipUD':
            img = np.flipud(img)
        elif self.p.param('Data Processing', 'iOrient').value() == 'flipLR':
            img = np.fliplr(img)
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot90':
            img = np.rot90(img, k=1)
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot180':
            img = np.rot90(img, k=2)
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot270':
            img = np.rot90(img, k=3)
        elif self.p.param('Data Processing', 'iOrient').value() == 'transpose':
            img = np.transpose(img)
        elif self.p.param('Data Processing', 'iOrient').value() == 'rot180 + tr':
            img = np.rot90(np.transpose(img), k=2)
            # self.trOrient = 'rot180 + tr'
        return img


    def maskValsAbove(self, img):
        if int(self.p.param('Data Processing', 'maskValsAbove').value()) > 0:
            img[img > int(self.p.param('Data Processing', 'maskValsAbove').value())] = 0
        return img

    def filterImages(self, ims):
        '''
        max or average filtering of an image range
        ims is the array of images to filter
        '''
        if self.currentFilter == 'average':
            filteredData = np.mean(ims, axis=0)
        elif self.currentFilter == 'max':
            #filteredData = np.maximum.reduce(ims, axis=0)
            filteredData = np.amax(ims, axis=0)  # the two seems to be equivalent, and same speed
        return filteredData

    def show1DPlotWindow(self):
        # if it does not yet exists add a window
        # the plot window may be used for Line Cuts as well as ROIs
        if hasattr(self, 'roiPlot'):
            self.roiPlot.show()
        else:
            self.roiPlot = self.win.addPlot(row=4, col=0, colspan=3)
            self.roiPlot.showGrid(x=True, y=True, alpha=.8)
            self.roiPlot.setMaximumHeight(150)
            self.win.show()
            self.show()
            self.LinePlotActive = True
            self.roiPlot.hoverEvent = self.ROIHoverEvent


    def hide1DPlotWindow(self):
        # hide if it is there
        # could also set all corresponding lists to empty ones
        # not sure what to do with the signals
        self.roiPlot.hide()
        self.win.show()
        self.show()
        self.LinePlotActive = False

    def addLineCut(self):
        # add an nth line cut to LineCuts, add to calculated areas, add to 1dplot, add signal
        n = len(self.lineCuts)
        self.lineCuts.append(pg.ROI([100, 300], [200, 1], pen=self.roiColors[n], invertible=True))
        self.lineCuts[n].addScaleHandle([0.5, 1], [0.5, 0.5])
        self.lineCuts[n].addScaleRotateHandle([1, 0.5], [0, 0.5])
        self.lineCuts[n].addScaleRotateHandle([0, 0.5], [1, 0.5])
        self.p3.addItem(self.lineCuts[n])
        self.lineCuts[n].setZValue(10)  # make sure ROI is drawn above image
        # add 1d plot
        self.lineCutsArea.append(self.lineCuts[n].getArrayRegion(self.showData, self.imgLeft))
        self.lineCutsCurves.append(self.roiPlot.plot(self.lineCutsArea[n].mean(axis=0), clear=False, pen=self.roiColors[n]))
        # print('Define ROI with pen: %s' % str(self.roiColors[rois]))
        self.lineCuts[n].sigRegionChanged.connect(self.lineCutsChanged)

        self.lineCutsChanged()

    def removeLineCut(self, every=False):
        # remove the last line cut from the lineCuts, from the calculated areas, from the 1dplot
        # if every is True, remove all defined lineCuts
        if every:
            while len(self.lineCuts) > 0:
                self.p3.removeItem(self.lineCuts[-1])
                del(self.lineCuts[-1])
                del(self.lineCutsArea[-1])
                self.roiPlot.removeItem(self.lineCutsCurves[-1])
                del(self.lineCutsCurves[-1])
        else:
            self.p3.removeItem(self.lineCuts[-1])
            del(self.lineCuts[-1])
            del(self.lineCutsArea[-1])
            self.roiPlot.removeItem(self.lineCutsCurves[-1])
            del(self.lineCutsCurves[-1])

    def addROI(self):
        # add roi to ROIS, add to calculated areas, add to 1dplot, add signal
        n = len(self.ROIs)
        self.ROIs.append(pg.ROI([100, 300], [100, 100], pen=self.roiColors[n], invertible=True))
        self.ROIs[n].addScaleHandle([0.5, 1], [0.5, 0.5])
        self.ROIs[n].addScaleHandle([1, 0.5], [0.5, 0.5])
        self.p3.addItem(self.ROIs[n])
        self.ROIs[n].setZValue(10)  # make sure ROI is drawn above image
        # add 1d plot
        self.ROIArea.append(self.ROIs[n].getArrayRegion(self.showData, self.imgLeft))
        self.ROICurves.append(self.roiPlot.plot(self.ROIArea[n].mean(axis=0), clear=False, pen=self.roiColors[n]))
        # print('Define ROI with pen: %s' % str(self.roiColors[rois]))
        self.ROIs[n].sigRegionChanged.connect(self.ROIChanged)

        self.ROIChanged()


    def removeROI(self, every=False):
        # remove the last ROI from the ROIS, from the calculated areas, from the 1dplot
        # if every is True, remove all defined ROIS
        if every:
            while len(self.ROIs) > 0:
                self.p3.removeItem(self.ROIs[-1])
                del(self.ROIs[-1])
                del(self.ROIArea[-1])
                self.roiPlot.removeItem(self.ROICurves[-1])
                del(self.ROICurves[-1])
        else:
            self.p3.removeItem(self.ROIs[-1])
            del(self.ROIs[-1])
            del(self.ROIArea[-1])
            self.roiPlot.removeItem(self.ROICurves[-1])
            del(self.ROICurves[-1])


    def showROI(self):
        '''
        TODO: This would need a refractoring!!!
        '''
        activeRegions = max(len(self.ROIs), len(self.lineCuts))
        if self.p.param('Data Processing', 'Line plots').value() != 'None':
            self.show1DPlotWindow()
        else:
            self.hide1DPlotWindow()
            self.removeLineCut(every=True)
            self.removeROI(every=True)

        if self.p.param('Data Processing', 'Line plots').value() == 'line cut' and len(self.ROIs) > 0:  # change to line cut directly from ROI
            self.removeROI(every=True)
            self.p.param('Data Processing', 'nROI').setValue(1)
            self.addLineCut()
        if self.p.param('Data Processing', 'Line plots').value() == 'ROI' and len(self.lineCuts) > 0:  # change to ROI directly from line cut
            self.removeLineCut(every=True)
            self.p.param('Data Processing', 'nROI').setValue(1)
            self.addROI()

        if self.p.param('Data Processing', 'nROI').value() > activeRegions:
            if self.p.param('Data Processing', 'Line plots').value() == 'line cut':
                # the while is necessary, because the sigValueChanged may combine fast changes to a single emission
                # could be implemented in the addLineCut function?
                while self.p.param('Data Processing', 'nROI').value() > len(self.lineCuts):
                    self.addLineCut()
            elif self.p.param('Data Processing', 'Line plots').value() == 'ROI':
                # the while is necessary, because the sigValueChanged may combine fast changes to a single emission
                # could be implemented in the addROI function?
                while self.p.param('Data Processing', 'nROI').value() > len(self.ROIs):
                    self.addROI()
        else:
            if self.p.param('Data Processing', 'Line plots').value() == 'line cut':
                # print('removeLineCuts called without every!')
                while self.p.param('Data Processing', 'nROI').value() < len(self.lineCuts):
                    self.removeLineCut()
            elif self.p.param('Data Processing', 'Line plots').value() == 'ROI':
                while self.p.param('Data Processing', 'nROI').value() < len(self.ROIs):
                    self.removeROI()

    def ROIChanged(self):
        for i, roi in enumerate(self.ROIs):
            roicurve = [np.sum(roi.getArrayRegion(self.ImageData[imno,:,:], self.imgLeft)) for imno in range(self.ImageData.shape[0])]
            self.ROICurves[i].setData(roicurve)

    def lineCutsChanged(self):
        for i, lineCut in enumerate(self.lineCuts):
            self.lineCutsArea[i] = lineCut.getArrayRegion(self.showData, self.imgLeft)
            self.lineCutsCurves[i].setData(self.lineCutsArea[i].mean(axis=0))

    def changeAutocolorscale(self):
        self.autoColorscale = self.p.param('Data Processing', 'autoColorscale').value()
        self.updateRegion()

    def changeFilter(self):
        self.currentFilter = self.p.param('Data Processing', 'rangeFilter').value()
        self.updateRegion()

    def updateTree(self):
        if self.p.param('Iso Line', 'show').value():
            self.p.param('Iso Line', 'iso').show()
        else:
            self.p.param('Iso Line', 'iso').hide()
        if self.p.param('Data Processing', 'Line plots').value() == 'None':
            self.p.param('Data Processing', 'nROI').hide()
            self.p.param('Data Processing', 'nROI').setValue(1)
        else:
            self.p.param('Data Processing', 'nROI').show()
        self.showROI()
        self.updateRegion()

    def changeImageNo(self):
        i = self.p.param('Data Processing', 'imageNo').value()
        self.imageRegion.setRegion((max(0, i-0.5), min(i+0.5, len(self.Images))))
        self.updateRegion()

    def updateImageRegion(self):
        '''
        this takes care of the linearRegionItems bounds and the labels
        '''
        fromImage = min(int(np.round(self.imageRegion.getRegion()[0])), self.ImageData.shape[0])
        toImage = min(int(np.round(self.imageRegion.getRegion()[1])), self.ImageData.shape[0])
        #print('from %d to %d' %(fromImage, toImage))
        self.currentImage = (fromImage, toImage)
        if fromImage == toImage-1:
            self.LabelL.setText("%s" % self.Images[fromImage].rpartition('/')[2])
        else:
            if self.currentFilter == 'average':
                self.LabelL.setText("Mean of images: %i:%i" % (fromImage*self.steps, toImage*self.steps))
            elif self.currentFilter == 'max':
                self.LabelL.setText("Max of images: %i:%i" % (fromImage*self.steps, toImage*self.steps))



    def updateRegion(self):
        self.imgLeft.show()
        self.imageRegion.setBounds = ([0, self.ImageData.shape[0]])
        self.imgLeft.resetTransform()
        #self.p3.getAxis('bottom').setScale(None)
        #self.p3.getAxis('left').setScale(None)
        self.p3.getAxis('bottom').enableAutoSIPrefix(True)
        self.p3.getAxis('left').enableAutoSIPrefix(True)
        self.p3.getAxis('bottom').setGrid(0)
        self.p3.getAxis('left').setGrid(0)

        self.updateImageRegion()

        fromImage = min(int(np.round(self.imageRegion.getRegion()[0])), self.ImageData.shape[0])
        toImage = min(int(np.round(self.imageRegion.getRegion()[1])), self.ImageData.shape[0])

        if len(self.ImageData.shape) == 3 and len(self.ImageData[self.currentImage[0]:self.currentImage[1], :, :]) > 0:
            self.showData = self.filterImages(self.ImageData[self.currentImage[0]:self.currentImage[1], :, :])
            self.showData = self.maskValsAbove(self.showData)
            self.showData = self.prepFinalImage(self.showData)
        else:
            self.showData = self.ImageData

        if self.autoColorscale:
            self.imgLeft.setImage(self.showData, autoLevels=True)
        else:
            self.imgLeft.setImage(self.showData, autoLevels=False)
        # self.statusLabel.setText('Updating isoline to %.1f' % self.p.param('Iso Line', 'iso').value())
        # self.progressBar.setMaximum(2)
        # self.progressBar.show()
        # self.progressBar.setValue(1)
        if self.p.param('Iso Line', 'show').value():
            self.iso.setLevel(self.p.param('Iso Line', 'iso').value())
            # self.iso.setData(pg.gaussianFilter(self.showData, (2, 2)))
            self.iso.setData(scipy.ndimage.gaussian_filter(self.showData, (2, 2)))
        else:
            self.iso.setData(None)

        self.lineCutsChanged()
        self.ROIChanged()
        # self.progressBar.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CBF(sys.argv)
    sys.exit(app.exec_())

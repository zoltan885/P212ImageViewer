#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: Hegedues
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


class CBF(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'CBF Viewer 0.2'
        self.Images = []
        # self.ImageData=np.zeros((1,1,1))
        # self.Images = '/'
        self.currentImage = 0
        self.currentFilter = 'average'
        self.autoColorscale = False
        self.ROI = []
        self.roiPlotActive = False
        self.knownFileTypes = ['tif', 'cbf']
        pg.setConfigOptions(imageAxisOrder='row-major')
        self.initUI()

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

    def loadImage(self):
        self.Images = QFileDialog.getOpenFileNames(self, "Open file", "/gpfs/current/raw/", "Image Files (*.cbf *.tif)")[0]
        self.steps = 1
        if len(self.Images) == 0:
            return 0
        assert self._checkSize(self.Images, maxOccupation=.8), 'Memory exceeded'
        SizeDummy = fabio.open(self.Images[0]).data
        xSize, ySize = SizeDummy.shape[0], SizeDummy.shape[1]
        self.ImageData = np.zeros([len(self.Images), xSize, ySize])
        self.statusLabel.setText('Loading %i images' % len(self.Images))
        self.progressBar.setMaximum(len(self.Images))
        self.progressBar.show()
        for i, filename in enumerate(self.Images):
            self.progressBar.setValue(i+1)
            self.update()
            self.ImageData[i, :, :] = np.flipud(fabio.open(filename).data)
        # self.imageRegion.setBounds = ([0, self.ImageData.shape[0]])
        self.progressBar.hide()
        self.statusLabel.setText(str(len(self.Images)) + ' images loaded')
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds([0, len(self.Images)])
        self.updateRegion()

    def loadFolder(self):
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", "/gpfs/current/raw/", QFileDialog.ShowDirsOnly)
        self.Images = np.sort(glob.glob(self.dir+'/*.cbf'))

        if len(self.Images) == 0:
            return 0
        try:
            self.Images = eval('self.Images[%s]' % self.p.param('Actions', 'Slicing').value())
        except ValueError:
            print('Slicing was not understood!')
        try:
            self.steps = int(str(self.p.param('Actions', 'Slicing').value()).rpartition(':')[2])
        except ValueError:
            self.steps = 1
        # assert self._checkSize(self.Images, maxOccupation=.8), 'Memory exceeded'
        self.progressBar.setMaximum(len(self.Images))
        self.progressBar.show()
        SizeDummy = fabio.open(self.Images[0]).data
        xSize, ySize = SizeDummy.shape[0], SizeDummy.shape[1]
        # print(xSize, ySize)
        self.statusLabel.setText('Loading %i images' % len(self.Images))
        self.ImageData = np.zeros([len(self.Images), xSize, ySize])
        for i, filename in enumerate(self.Images):
            self.progressBar.setValue(i+1)
            self.update()
            self.ImageData[i, :, :] = np.flipud(fabio.open(filename).data)
        self.statusLabel.setText(str(len(self.Images)) + ' images loaded')
        #print(self.ImageData.shape[0])
        self.progressBar.hide()
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds((0, len(self.Images)))
        self.updateRegion()

    def loadFolderMapped(self):
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", "/gpfs/current/raw/", QFileDialog.ShowDirsOnly)
        self.Images = np.sort(glob.glob(self.dir+'/*.tif'))
        if len(self.Images) == 0:
            return 0
        try:
            self.Images = eval('self.Images[%s]' % self.p.param('Actions', 'Slicing').value())
        except ValueError:
            print('Slicing was not understood!')
        try:
            self.steps = int(str(self.p.param('Actions', 'Slicing').value()).rpartition(':')[2])
        except ValueError:
            self.steps = 1

        self.progressBar.setMaximum(len(self.Images))
        self.progressBar.show()
        SizeDummy = fabio.open(self.Images[0]).data
        xSize, ySize = SizeDummy.shape[0], SizeDummy.shape[1]

        self.ImageData = np.memmap('/tmp/memmap.npy', dtype='float32', mode='w+', shape=(len(self.Images), xSize, ySize))
        for i, filename in enumerate(self.Images):
            self.progressBar.setValue(i+1)
            self.update()
            self.ImageData[i, :, :] = np.flipud(fabio.open(filename).data)
        self.statusLabel.setText(str(len(self.Images)) + ' images loaded')
        #print(self.ImageData.shape[0])
        self.progressBar.hide()
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds((0, len(self.Images)))
        self.updateRegion()




    def loadFolderWithDark(self):
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", "/gpfs/current/raw/", QFileDialog.ShowDirsOnly)
        self.Images = np.sort(glob.glob(self.dir+'/*.cbf'))
        self.Darks = [i for i in self.Images if 'dark' in i]
        self.Images = [i for i in self.Images if 'dark' not in i]  # if there are dark images in the folder don't use them
        self.Dark = None
        if len(self.Darks) > 0:
            self.Dark = np.flipud(fabio.open(self.Darks[0]).data)

        if len(self.Images) == 0:
            return 0
        try:
            self.Images = eval('self.Images[%s]' % self.p.param('Actions', 'Slicing').value())
        except ValueError:
            print('Slicing was not understood!')
        try:
            self.steps = int(str(self.p.param('Actions', 'Slicing').value()).rpartition(':')[2])
        except ValueError:
            self.steps = 1
        # assert self._checkSize(self.Images, maxOccupation=.8), 'Memory exceeded'
        self.progressBar.setMaximum(len(self.Images))
        self.progressBar.show()
        SizeDummy = fabio.open(self.Images[0]).data
        xSize, ySize = SizeDummy.shape[0], SizeDummy.shape[1]
        # print(xSize, ySize)
        self.statusLabel.setText('Loading %i images' % len(self.Images))
        self.ImageData = np.zeros([len(self.Images), xSize, ySize])
        for i, filename in enumerate(self.Images):
            self.progressBar.setValue(i+1)
            self.update()
            if self.Dark is not None:
                self.ImageData[i, :, :] = np.flipud(fabio.open(filename).data).astype(np.float32)-self.Dark
            else:
                self.ImageData[i, :, :] = np.flipud(fabio.open(filename).data)
        self.statusLabel.setText(str(len(self.Images)) + ' images loaded')
        #print(self.ImageData.shape[0])
        self.progressBar.hide()
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds((0, len(self.Images)))
        self.updateRegion()

    def loadFolderTif(self):
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", "/gpfs/current/raw/", QFileDialog.ShowDirsOnly)
        self.Images = np.sort(glob.glob(self.dir+'/*.tif'))
        if len(self.Images) == 0:
            return 0
        try:
            self.Images = eval('self.Images[%s]' % self.p.param('Actions', 'Slicing').value())
        except ValueError:
            print('Slicing was not understood!')
        try:
            self.steps = int(str(self.p.param('Actions', 'Slicing').value()).rpartition(':')[2])
        except ValueError:
            self.steps = 1
        assert self._checkSize(self.Images, maxOccupation=.8), 'Memory exceeded'
        self.progressBar.setMaximum(len(self.Images))
        self.progressBar.show()
        SizeDummy = fabio.open(self.Images[0]).data
        xSize, ySize = SizeDummy.shape[0], SizeDummy.shape[1]
        # print(xSize, ySize)
        self.statusLabel.setText('Loading %i images' % len(self.Images))
        self.ImageData = np.zeros([len(self.Images), xSize, ySize])
        for i, filename in enumerate(self.Images):
            self.progressBar.setValue(i+1)
            self.update()
            self.ImageData[i, :, :] = np.flipud(fabio.open(filename).data)
        self.statusLabel.setText(str(len(self.Images)) + ' images loaded')
        #print(self.ImageData.shape[0])
        self.progressBar.hide()
        self.imageRegion.setRegion((0, 1))
        self.imageRegion.setBounds((0, len(self.Images)))
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
                {'name': 'Load Image', 'type': 'action'},
                {'name': 'Load Folder', 'type': 'action'},
                {'name': 'Load Folder Mem', 'type': 'action'},
                {'name': 'Load Folder WD', 'type': 'action'},
                {'name': 'Load Folder tif', 'type': 'action'},
                {'name': 'Slicing', 'type': 'str', 'value': '0:None:1', 'step': 1},
                # {'name': 'Dark Image', 'type': 'action'},
                # {'name': 'Mask Image', 'type': 'action'},
            ]},
            {'name': 'Data Processing', 'type': 'group', 'children': [
                {'name': 'iOrient', 'type': 'list', 'values': ['none', 'flipUD', 'flipLR', 'transpose', 'rot90', 'rot180', 'rot270', 'rot180 + tr']},
                {'name': 'maskValsAbove', 'type': 'float', 'value': 0, 'step': 100.},

                {'name': 'rangeFilter', 'type': 'list', 'values': ['average', 'max']},
                {'name': 'autoColorscale', 'type': 'bool', 'value': False},
                {'name': 'roi', 'type': 'bool', 'value': False},
                {'name': 'Line plots', 'type': 'list', 'values': ['', 'line cut', 'ROI']},
                {'name': 'nROI', 'type': 'int', 'value': 1, 'step': 1, 'bounds': (0, 4), 'visible': False},
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
        self.p.param('Actions', 'Load Image').sigActivated.connect(self.loadImage)
        self.p.param('Actions', 'Load Folder').sigActivated.connect(self.loadFolder)
        self.p.param('Actions', 'Load Folder Mem').sigActivated.connect(self.loadFolderMapped)
        self.p.param('Actions', 'Load Folder WD').sigActivated.connect(self.loadFolderWithDark)
        self.p.param('Actions', 'Load Folder tif').sigActivated.connect(self.loadFolderTif)
        self.p.param('Data Processing', 'iOrient').sigValueChanged.connect(self.updateRegion)
        self.p.param('Data Processing', 'maskValsAbove').sigValueChanged.connect(self.updateRegion)
        self.p.param('Data Processing', 'rangeFilter').sigValueChanged.connect(self.changeFilter)
        self.p.param('Data Processing', 'autoColorscale').sigValueChanged.connect(self.changeAutocolorscale)
        #self.p.param('Data Processing', 'roi').sigValueChanged.connect(self.showROI)
        self.p.param('Data Processing', 'Line plots').sigStateChanged.connect(self.updateTree)
        #self.p.param('Data Processing', 'Line plots').sigStateChanged.connect(self.showROI)
        self.p.param('Data Processing', 'nROI').sigValueChanged.connect(self.showROI)
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
        self.imageRegion = pg.LinearRegionItem(bounds=[0, None])
        self.imageRegion.sigRegionChanged.connect(self.updateRegion)  # this calls the internal updateRegion and not the self.updateRegion!!!

        self.p2.setMaximumHeight(80)
        self.p2.addItem(self.imageRegion)
        self.p2.showAxis('left', show=False)

        self.p3 = self.win.addPlot(row=0, col=0)
        self.imgLeft = pg.ImageItem()
        self.p3.getViewBox().setAspectLocked(True)
        self.p3.addItem(self.imgLeft)

        self.iso = pg.IsocurveItem(level=0.8, pen='g')
        self.iso.setParentItem(self.imgLeft)
        self.iso.setZValue(self.p.param('Iso Line', 'iso').value())
        self.p.param('Iso Line', 'iso').hide()

        #self.p.param('Data Processing', 'nROI').hide()

        # self.p4 = win.addPlot(row=2, col=0)
        # self.p4.hide()


        # self.ctrROI=pg.LineROI([0, 5], [0, 0], width=2, pen=(1,9))

        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.imgLeft)
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
        i = int(np.clip(i, 0, self.ImageData.shape[1] - 1))
        j = int(np.clip(j, 0, self.ImageData.shape[2] - 1))
        val = np.mean(self.ImageData[self.currentImage[0]:self.currentImage[1], i, j])
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
            geometric
        This transforms all images, which does not make sense at all!!!
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
        so far it is done in the self.updateRegion function
        ims is the array of images to filter
        '''
        if self.currentFilter == 'average':
            filteredData = np.mean(ims, axis=0)
        elif self.currentFilter == 'max':
            filteredData = np.maximum.reduce(ims, axis=0)
        return filteredData

    def showROI(self):

        self.roiColors = ((0, 9), (0, 7), (0, 5), (0, 3))  # for several ROIs eventually
        rois = len(self.ROI) # number of currently requested rois
        if self.p.param('Data Processing', 'Line plots').value() != '' and self.p.param('Data Processing', 'nROI').value() > 0:
            #self.win.nextRow()
            if self.roiPlotActive is False: # plot is switched on
                self.roiPlot = self.win.addPlot(row=4, col=0, colspan=3)
                self.roiPlot.showGrid(x=True, y=True, alpha=.8)
                self.roiPlot.setMaximumHeight(150)
                self.win.show()
                self.show()
                self.roiPlotActive = True
                rois = 0

            if self.p.param('Data Processing', 'nROI').value() > rois:
                self.ROI.append(pg.ROI([100, 200], [200, 1], pen=self.roiColors[rois]))
                self.ROI[rois].addScaleHandle([0.5, 1], [0.5, 0.5])
                self.ROI[rois].addScaleRotateHandle([1, 0.5], [0, 0.5])
                self.ROI[rois].addScaleRotateHandle([0, 0.5], [1, 0.5])
                self.p3.addItem(self.ROI[rois])
    
                self.ROI[rois].setZValue(10)  # make sure ROI is drawn above image
                self.ROI[rois].sigRegionChanged.connect(self.ROIchanged)
                self.ROIchanged()
            else:
                self.p3.removeItem(self.ROI[-1])
                del(self.ROI[-1])
        else:
            for r in self.ROI:
                self.p3.removeItem(r)
            self.ROI = []
            try:
                self.roiPlot.hide()
            except Exception:
                pass
            self.win.show()
            self.show()
            self.roiPlotActive = False

        # this is to show the mouse values
        self.roiPlot.hoverEvent = self.ROIHoverEvent

    def ROIchanged(self):
        for i,roi in enumerate(self.ROI):
            roiarea = roi.getArrayRegion(self.showData, self.imgLeft)
            self.roiPlot.plot(roiarea.mean(axis=0), clear=True, pen=self.roiColors[i])

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
        if self.p.param('Data Processing', 'Line plots').value() == '':
            self.p.param('Data Processing', 'nROI').hide()
            self.p.param('Data Processing', 'nROI').setValue(1)
        else:
            self.p.param('Data Processing', 'nROI').show()
            self.showROI()
        self.updateRegion()

    def updateRegion(self):
        self.imgLeft.show()
        self.imageRegion.setBounds = ([0, self.ImageData.shape[0]])
        self.imgLeft.resetTransform()
        self.p3.getAxis('bottom').setScale(None)
        self.p3.getAxis('left').setScale(None)
        self.p3.getAxis('bottom').setGrid(0)
        self.p3.getAxis('left').setGrid(0)

        fromImage = min(int(np.round(self.imageRegion.getRegion()[0])), self.ImageData.shape[0])
        toImage = min(int(np.round(self.imageRegion.getRegion()[1])), self.ImageData.shape[0])
        self.currentImage = (fromImage, toImage)
        if self.currentImage[0] == self.currentImage[1]-1:
            # self.p3.setTitle("%s" % self.Images[self.currentImage[0]].rpartition('/')[2])
            self.LabelL.setText("%s" % self.Images[self.currentImage[0]].rpartition('/')[2])
            # self.p3.setTitle("Image %i" % (self.currentImage[0]*self.binning))
        else:
            if self.currentFilter == 'average':
                # self.p3.setTitle("Mean of images: %i:%i" % (self.currentImage[0]*self.steps, self.currentImage[1]*self.steps))
                self.LabelL.setText("Mean of images: %i:%i" % (self.currentImage[0]*self.steps, self.currentImage[1]*self.steps))
            elif self.currentFilter == 'max':
                # self.p3.setTitle("Max of images: %i:%i" % (self.currentImage[0]*self.steps, self.currentImage[1]*self.steps))
                self.LabelL.setText("Max of images: %i:%i" % (self.currentImage[0]*self.steps, self.currentImage[1]*self.steps))

        if len(self.ImageData[fromImage:toImage, :, :]) > 0:
            self.showData = self.filterImages(self.ImageData[fromImage:toImage, :, :])
            self.showData = self.maskValsAbove(self.showData)
            #if int(self.p.param('Data Processing', 'maskValsAbove').value()) > 0:
            #    self.showData[self.showData > int(self.p.param('Data Processing', 'maskValsAbove').value())] = 0

            self.showData = self.prepFinalImage(self.showData)

            if self.autoColorscale:
                self.imgLeft.setImage(self.showData, autoLevels=True)
            else:
                self.imgLeft.setImage(self.showData, autoLevels=False)
        else:
            self.showData = self.ImageData[0]

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

        if self.ROI is not None:
            self.ROIchanged()

        # self.progressBar.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CBF()
    sys.exit(app.exec_())

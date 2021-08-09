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

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QLabel, QProgressBar
#from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys, os
import numpy as np
#import psutil, resource, time
import time

from version import NAME, VERSION, copyrightNotice
from settings import baseFolder
#from dataClass import dataClass
from aux import MemoryMonitorClass, ImageDataClass


DIM = (500, 500)


class StateClass():
    '''
    Class supposed to hold all state related information of a Data object
    
    When several datasets (tabs/windows) are open at the same time the GUI 
    should know the current settings for each separately.
    '''
    def __init__(self, name):
        self.name = name
        self.currentImage = 0
        self.checkBox_fixAspect = True
        self.checkBox_autoColor = True
        self.checkBox_subtract = False
        self.checkBox_divide = False

    def updateState(self):
        pass

    def loadState(self):
        pass



class tabContent(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        uic.loadUi('tabWidget.ui', self)
        self.Data = kwargs['dataClass']
        self.glw = self.GrphicsLayoutWidget
        self.glw.setBackground('k')
        self.plotItem = self.glw.addPlot(row=0, colspan=2)
        self.plotItem.getViewBox().setAspectLocked(True)
        self.img = pg.ImageItem()
        self.plotItem.addItem(self.img)
        self.img.setImage(self.Data.plotData, autoLevels=True)
        self.img.show()

        self.hist = pg.HistogramLUTItem(image=self.img)
        self.glw.addItem(self.hist, row=0, col=2)

        self.labelL = self.glw.addLabel(text='', row=4, col=0, colspan=1, justify='right')
        self.labelR = self.glw.addLabel(text='', row=4, col=1, colspan=1, justify='right')
        self.labelL.setText('')
        self.labelR.setText('')

        self.glw1d = self.GrphicsLayoutWidget1D
        self.glw.setBackground('k')
        self.roiPlot = self.glw1d.addPlot(row=0, col=0, colspan=2)
        self.roiPlot.showGrid(x=True, y=True, alpha=.8)
        self.labelL1D = self.glw1d.addLabel(text='', row=1, col=0, colspan=1, justify='left')
        self.labelR1D = self.glw1d.addLabel(text='', row=1, col=1, colspan=1, justify='right')
        self.labelL1D.setText('')
        self.labelR1D.setText('')
        self.glw1d.hide()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(copyrightNotice)
        uic.loadUi('future3b.ui', self)
        self.setWindowTitle('%s %i.%i' % (NAME, VERSION['major'], VERSION['minor']+1))
        # self.setWindowIcon(QtGui.QIcon('icon/icon32.png'))

        pg.setConfigOptions(imageAxisOrder='row-major')

        self.dark = np.ones(DIM)
        self.dark[:100, :100] = 2
        self.white = np.ones(DIM)
        self.white[300:700, 300:700] = 2

        self.dataDict = {}
        
        # LINE CUTS
        self.LinePlotActive = False
        self.roiColors = ("FF0000", (2, 9), (5, 9), (7, 9))  # for several ROIs eventually
        self.ROIs = []  # visualization
        self.ROIArea = []  # area used to calculate
        self.ROICurves = []  # 1D curve
        self.lineCuts = []
        self.lineCutsArea = []
        self.lineCutsCurves = []


        # SETTINGS
        self.autoColorscale = True

        self.PID = os.getpid()
        self.prepare()



    def prepare(self):

        # STATUS BAR SETTINGS
        self.statusUsageLabel = QLabel()
        self.statusBar().addPermanentWidget(self.statusUsageLabel)

        # SETUP MEMORY AND CPU USAGE IN THE STATUS BAR
        self.memthread = QThread()
        self.memoryMonitor = MemoryMonitorClass()
        self.memoryMonitor.moveToThread(self.memthread)
        self.memoryMonitor.usageSignal.connect(self.reportMemory2)
        self.memthread.started.connect(self.memoryMonitor.run)
        self.memthread.start()

        self.actionLoad_Dummy.triggered.connect(self.generateWithClass)
        self.actionLoad_Folder.triggered.connect(self.loadWithClass)
        self.actionQuit.triggered.connect(self.leaveProgram)

        return

        self.glw = self.GrphicsLayoutWidget
        self.glw.setBackground('k')
        self.plotItem = self.glw.addPlot(row=0, colspan=2)
        self.plotItem.getViewBox().setAspectLocked(True)
        self.checkBox_fixAspect.setChecked(True)
        self.img = pg.ImageItem()
        self.plotItem.addItem(self.img)
        self.img.setImage(self.showData, autoLevels=self.autoColorscale)
        self.img.show()
        self.actionLight_Background.changed.connect(self.toggleBg)

        # IMAGE
        self.checkBox_fixAspect.stateChanged.connect(self.fixingAspect)
        self.checkBox_autoColor.setChecked(self.autoColorscale)
        self.checkBox_autoColor.stateChanged.connect(self.autoColorscaleSetter)
        self.comboBox_transform.currentTextChanged.connect(self.updateImage)
        self.checkBox_maskBelow.stateChanged.connect(self.updateImage)
        #self.doubleSpinBox_maskBelow.editingFinished.connect(self.updateImage)  # would be more elegant, not emitted when the arrows are used
        self.doubleSpinBox_maskBelow.valueChanged.connect(self.updateImage)
        self.checkBox_maskAbove.stateChanged.connect(self.updateImage)
        self.doubleSpinBox_maskAbove.valueChanged.connect(self.updateImage)

        self.hist = pg.HistogramLUTItem(image=self.img)
        self.glw.addItem(self.hist, row=0, col=2)
        #self.hist.sigLevelsChanged.connect(self.noAutoColor) # can not really work, see note at the function
        #self.hist.sigLevelChangeFinished.connect(self.noAutoColor) # this is also okay, but looks lazy

        # BACKGROUND
        self.checkBox_subtract.stateChanged.connect(self.updateImage)
        self.checkBox_divide.stateChanged.connect(self.updateImage)

        # RANGE
        self.checkBox_fullStack.setEnabled(False)
        self.label_rangeFilter.setEnabled(False)
        self.comboBox_filter.setEnabled(False)
        self.label_rangeStart.setText('Image no')
        self.label_rangeFinish.hide()
        self.spinBox_rangeFinish.setEnabled(False)
        # enable on ticking the box
        self.checkBox_useRange.stateChanged.connect(self.enableRange)
        self.comboBox_filter.currentTextChanged.connect(self.updateImage)
        self.checkBox_fullStack.stateChanged.connect(self.fullStackFilter)

        # RANGE SLIDER
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(1)  # this is kind of a placeholder
        self.horizontalSlider.setValue((0,))
        self.horizontalSlider.valueChanged.connect(self.sliderChanged)
        self.horizontalSlider.valueChanged.connect(self.updateImage)
        self.horizontalSlider.hide()
        self.spinBox_rangeStart.editingFinished.connect(self.updateSlider)
        self.spinBox_rangeFinish.editingFinished.connect(self.updateSlider)

        # TOOLBOX
        self.actionVisible_Image_Manipulation.setChecked(True)
        self.frame.show()
        self.actionVisible_Image_Manipulation.changed.connect(self.visibleImageToolbar)


        # IMAGE HOVER LABELS
        self.labelL = self.glw.addLabel(text='', row=4, col=0, colspan=1, justify='right')
        self.labelR = self.glw.addLabel(text='', row=4, col=1, colspan=1, justify='right')
        self.labelL.setText('')
        self.labelR.setText('')
        # IMAGE HOVER
        self.img.hoverEvent = self.imageHoverEvent



        # Load in different thread & progressBar
        # self.actionLoad_Image.triggered.connect(self.load)

        # Load ThreadPool & progressBar
        # self.actionLoad_Folder.triggered.connect(self.loadThreadPool)


        # self.imageDataSet.dataGenerate.signals.finished.connect(self.loadWithClassResult)



        # LINE CUTS AND ROIS
        # self.pushButton.clicked.connect(self.show1DPlotWindow)
        # self.pushButton_2.clicked.connect(self.gwbs)
        self.spinBox_ROI.setEnabled(False)
        self.comboBox_ROI.currentTextChanged.connect(self.showROI)
        self.spinBox_ROI.editingFinished.connect(self.showROI)

        self.glw1d = self.GrphicsLayoutWidget1D
        self.glw.setBackground('k')
        self.roiPlot = self.glw1d.addPlot(row=0, col=0, colspan=2)
        self.roiPlot.showGrid(x=True, y=True, alpha=.8)
        self.labelL1D = self.glw1d.addLabel(text='', row=1, col=0, colspan=1, justify='left')
        self.labelR1D = self.glw1d.addLabel(text='', row=1, col=1, colspan=1, justify='right')
        self.labelL1D.setText('')
        self.labelR1D.setText('')
        self.roiPlot.hoverEvent = self.ROIHoverEvent
        self.glw1d.hide()


    def gwbs(self):
        print(self.plotItem.getViewBox().state)

    def generateWithClass(self):
        self.tabWidget.setTabText(0, self.imageDataSet.name)
        self.tabWidget.addTab(tabContent(dataClass=self.imageDataSet), 'new tab')
        self.imageDataSet.dataGenerate.signals.started.connect(self.addProgressBar)
        self.imageDataSet.dataGenerate.signals.progress.connect(self.updateProgressBar)
        self.imageDataSet.dataGenerate.signals.finished.connect(self.removeProgressBar)
        self.imageDataSet.signals.chunkLoaded.connect(self._intermediateLoadState)
        self.imageDataSet.generate()

    def loadWithClass(self):
        '''
        load data, create DATA, State, TabContentWidget and LineCut/ROI for each new set

        '''
        sn = 'dataset1'
        self.dataDict[sn] = {'data': None, 'tcw': None, 'state': None, 'line': None, 'roi': None}
        self.dataDict[sn]['data'] = ImageDataClass()
        self.dataDict[sn]['tcw'] = tabContent(dataClass=self.dataDict[sn]['data'])
        self.tabWidget.addTab(self.dataDict[sn]['tcw'], sn)
        if self.tabWidget.tabText(0) == 'DefaultData1':
            self.tabWidget.removeTab(0)
        self.dataDict[sn]['data'].dataFolderLoad.signals.started.connect(self.addProgressBar)
        self.dataDict[sn]['data'].dataFolderLoad.signals.progress.connect(self.updateProgressBar)
        self.dataDict[sn]['data'].dataFolderLoad.signals.finished.connect(self.removeProgressBar)
        self.dataDict[sn]['data'].signals.chunkLoaded.connect(self._intermediateLoadState)
        self.dataDict[sn]['data'].loadFolder()



    # def loadWithClassResult(self):
    #     print('Finished data geneartion with new class: %s' % self.imageDataSet.name)
    #     print('Genarated data dimensions:')
    #     print(self.imageDataSet.data.shape)
    #     self.horizontalSlider.setMaximum(self.imageDataSet.data.shape[0]-1)
    #     self.horizontalSlider.show()
    #     self.statusBar().showMessage('Loaded %d images' % self.imageDataSet.data.shape[0])
    #     self.updateImage()

    def _intermediateLoadState(self):
        # print('Genarated data dimensions:')
        # print(self.imageDataSet.data.shape)
        self.dataDict['dataset1']['tcw'].rangeSlider.setMaximum(self.dataDict['dataset1']['data'].data.shape[0]-1)
        self.dataDict['dataset1']['tcw'].rangeSlider.show()
        #self.horizontalSlider.setMaximum(self.imageDataSet.data.shape[0]-1)
        #self.horizontalSlider.show()
        self.statusBar().showMessage('Loaded %d images' % self.dataDict['dataset1']['data'].data.shape[0])
        #print('updateImage()')
        #print('Data shape:')
        #print(self.imageDataSet.data.shape)
        self.updateImage()

    # def loadThreadPool(self):
    #     '''
    #     test function to load data with QThreadPool
    #     '''
    #     self.threadpool = QThreadPool()
    #     dataGenerate = DataGenerateClass(size=100)
    #     dataGenerate.signals.started.connect(self.addProgressBar)
    #     dataGenerate.signals.result.connect(self.updateThreadData)   # change this to update the data class
    #     dataGenerate.signals.progress.connect(self.updateProgressBar)
    #     dataGenerate.signals.finished.connect(self.removeProgressBar)
    #     self.threadpool.start(dataGenerate)


    # def updateThreadData(self, data):
    #     name = 'name'  # this is the name of the dataset
    #     if name not in self.dataDict.keys():
    #         self.dataDict[name] = data
    #     else:
    #         self.dataDict[name] = np.concatenate((self.dataDict[name], data))



    # def load(self):
    #     '''
    #     test function to load data with separate thread
    #     '''
    #     self.loadThread = QThread()
    #     self.loading = DataLoadClass()
    #     self.loading.moveToThread(self.loadThread)
    #     self.loading.dataLoadSignal.connect(self.updateProgressBar)
    #     self.loading.dataLoadStartSignal.connect(self.addProgressBar)
    #     self.loading.dataLoadFinishedSignal.connect(self.removeProgressBar)
    #     # destroy thread at the end of loading!
    #     self.loading.dataLoadFinishedSignal.connect(self.loadThread.quit)
    #     self.loading.dataLoadFinishedSignal.connect(self.loading.deleteLater)
    #     self.loading.dataLoadFinishedSignal.connect(self.loadThread.deleteLater)

    #     self.loadThread.started.connect(self.loading.run)
    #     self.loadThread.start()



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
            self.glw1d.setBackground('w')
        else:
            self.glw.setBackground('k')
            self.glw1d.setBackground('k')

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
            # self.checkBox.setChecked(False)

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
            self.spinBox_rangeFinish.setEnabled(True)
            self.checkBox_fullStack.setEnabled(True)

            currImNo = self.horizontalSlider.value()[0]
            self.horizontalSlider.setValue((currImNo-3, currImNo+3))
            self.horizontalSlider.LabelPosition.LabelsAbove
        else:
            self.label_rangeFilter.setEnabled(False)
            self.comboBox_filter.setEnabled(False)
            self.label_rangeStart.setText('Image no')
            self.label_rangeFinish.hide()
            self.spinBox_rangeFinish.setEnabled(False)
            self.spinBox_rangeFinish.setValue(0)
            self.checkBox_fullStack.setChecked(False)  # this calls the self.fullStackFilter; stuff gets enabled
            self.checkBox_fullStack.setEnabled(False)

            currImNo = (self.horizontalSlider.value()[0] +
                        self.horizontalSlider.value()[1]) //2
            self.horizontalSlider.setValue((currImNo,))

    def fullStackFilter(self):
        '''
        sets the filtering for the full image stack
        '''
        if self.checkBox_fullStack.isChecked():
            self.horizontalSlider.setEnabled(False)
            self.spinBox_rangeStart.setEnabled(False)
            self.spinBox_rangeFinish.setEnabled(False)
        else:
            self.horizontalSlider.setEnabled(True)
            self.spinBox_rangeStart.setEnabled(True)
            self.spinBox_rangeFinish.setEnabled(True)
        self.updateImage()

    def updateSlider(self):
        if self.checkBox_useRange.isChecked():
            self.horizontalSlider.setValue((self.spinBox_rangeStart.value(),
                                              self.spinBox_rangeFinish.value()))
        else:
            self.horizontalSlider.setValue((self.spinBox_rangeStart.value(),))

    def sliderChanged(self):
        self.spinBox_rangeStart.setValue(self.horizontalSlider.value()[0])
        if self.checkBox_useRange.isChecked():
            self.spinBox_rangeFinish.setValue(self.horizontalSlider.value()[1])
        else:
            self.spinBox_rangeFinish.setValue(0)


#######################################


    def addLineCut(self):
        # add an nth line cut to LineCuts, add to calculated areas, add to 1dplot, add signal
        n = len(self.lineCuts)
        view = self.plotItem.getViewBox().state['viewRange']  # [[xmin,xmax],[ymin,ymax]]
        x0,y0 = (view[0][1]+9*view[0][0])/10, (view[1][1]+9*view[1][0])/10
        xspan = (view[0][1]-view[0][0])/2
        self.lineCuts.append(pg.ROI([x0, y0], [xspan, 1], pen={'color': self.roiColors[n], 'width': 2}, invertible=True))
        # self.lineCuts.append(pg.ROI([100, 300], [200, 1], pen=self.roiColors[n], invertible=True))
        self.lineCuts[n].addScaleHandle([0.5, 1], [0.5, 0.5])
        self.lineCuts[n].addScaleRotateHandle([1, 0.5], [0, 0.5])
        self.lineCuts[n].addScaleRotateHandle([0, 0.5], [1, 0.5])
        self.plotItem.addItem(self.lineCuts[n])
        self.lineCuts[n].setZValue(10)  # make sure ROI is drawn above image
        # add 1d plot
        self.lineCutsArea.append(self.lineCuts[n].getArrayRegion(self.showData, self.img))
        self.lineCutsCurves.append(self.roiPlot.plot(self.lineCutsArea[n].mean(axis=0), clear=False, pen=self.roiColors[n]))
        # print('Define ROI with pen: %s' % str(self.roiColors[rois]))
        self.lineCuts[n].sigRegionChanged.connect(self.lineCutsChanged)
        self.lineCutsChanged()

    def removeLineCut(self, every=False):
        # remove the last line cut from the lineCuts, from the calculated areas, from the 1dplot
        # if every is True, remove all defined lineCuts
        if every:
            while len(self.lineCuts) > 0:
                self.plotItem.removeItem(self.lineCuts[-1])
                del(self.lineCuts[-1])
                del(self.lineCutsArea[-1])
                self.roiPlot.removeItem(self.lineCutsCurves[-1])
                del(self.lineCutsCurves[-1])
        else:
            self.plotItem.removeItem(self.lineCuts[-1])
            del(self.lineCuts[-1])
            del(self.lineCutsArea[-1])
            self.roiPlot.removeItem(self.lineCutsCurves[-1])
            del(self.lineCutsCurves[-1])

    def addROI(self):
        # add roi to ROIS, add to calculated areas, add to 1dplot, add signal
        n = len(self.ROIs)
        view = self.plotItem.getViewBox().state['viewRange']  # [[xmin,xmax],[ymin,ymax]]
        x0,y0 = (view[0][1]+9*view[0][0])/10, (view[1][1]+9*view[1][0])/10
        xspan = (view[0][1]-view[0][0])/8
        yspan = (view[1][1]-view[1][0])/8
        self.ROIs.append(pg.ROI([x0, y0], [xspan, yspan], pen={'color': self.roiColors[n], 'width': 2}, invertible=True))
        # self.ROIs.append(pg.ROI([100, 300], [100, 100], pen=self.roiColors[n], invertible=True))
        self.ROIs[n].addScaleHandle([0.5, 1], [0.5, 0.5])
        self.ROIs[n].addScaleHandle([1, 0.5], [0.5, 0.5])
        self.plotItem.addItem(self.ROIs[n])
        self.ROIs[n].setZValue(10)  # make sure ROI is drawn above image
        # add 1d plot
        self.ROIArea.append(self.ROIs[n].getArrayRegion(self.showData, self.img))
        self.ROICurves.append(self.roiPlot.plot(self.ROIArea[n].mean(axis=0), clear=False, pen=self.roiColors[n]))
        # print('Define ROI with pen: %s' % str(self.roiColors[rois]))
        self.ROIs[n].sigRegionChanged.connect(self.ROIChanged)

        self.ROIChanged()


    def removeROI(self, every=False):
        # remove the last ROI from the ROIS, from the calculated areas, from the 1dplot
        # if every is True, remove all defined ROIS
        if every:
            while len(self.ROIs) > 0:
                self.plotItem.removeItem(self.ROIs[-1])
                del(self.ROIs[-1])
                del(self.ROIArea[-1])
                self.roiPlot.removeItem(self.ROICurves[-1])
                del(self.ROICurves[-1])
        else:
            self.plotItem.removeItem(self.ROIs[-1])
            del(self.ROIs[-1])
            del(self.ROIArea[-1])
            self.roiPlot.removeItem(self.ROICurves[-1])
            del(self.ROICurves[-1])


    def lineCutsChanged(self):
        for i, lineCut in enumerate(self.lineCuts):
            self.lineCutsArea[i] = lineCut.getArrayRegion(self.showData, self.img)
            self.lineCutsCurves[i].setData(self.lineCutsArea[i].mean(axis=0))

    def ROIChanged(self):
        for i, roi in enumerate(self.ROIs):
            roicurve = [np.sum(roi.getArrayRegion(self.imageDataSet.data[imno,:,:], self.img)) for imno in range(self.imageDataSet.data.shape[0])]
            self.ROICurves[i].setData(roicurve)


    def ROIHoverEvent(self, event):
        if event.isExit():
            self.labelR1D.setText('')
        else:
            pos = event.pos()
            mappedPos = self.roiPlot.vb.mapSceneToView(pos)
            x, y = mappedPos.x(), mappedPos.y()
            self.labelR1D.setText('%.3f %.3f' % (x, y))

    def showROI(self):
        '''

        '''
        activeRegions = max(len(self.ROIs), len(self.lineCuts))
        if self.comboBox_ROI.currentText() not in ['None', 'none']:
            self.glw1d.show()
            self.spinBox_ROI.setEnabled(True)
            self.LinePlotActive = True
        else:
            self.glw1d.hide()
            # self.hide1DPlotWindow()
            self.removeLineCut(every=True)
            self.removeROI(every=True)
            self.spinBox_ROI.setEnabled(False)
            self.LinePlotActive = False
            self.comboBox_transform.setEnabled(True)


        if self.comboBox_ROI.currentText() == 'Line cut' and len(self.ROIs) > 0:  # change to line cut directly from ROI
            self.removeROI(every=True)
            self.spinBox_ROI.setValue(1)
            self.addLineCut()
            self.comboBox_transform.setEnabled(True)
        if self.comboBox_ROI.currentText() == 'ROI' and len(self.lineCuts) > 0:  # change to ROI directly from line cut
            self.removeLineCut(every=True)
            self.spinBox_ROI.setValue(1)
            self.addROI()
            # disable visible image transformations
            self.comboBox_transform.setText('none')  # TODO make this work
            self.comboBox_transform.setEnabled(False)

        if self.spinBox_ROI.value() > activeRegions:
            if self.comboBox_ROI.currentText() == 'Line cut':
                # the while is necessary, because the sigValueChanged may combine fast changes to a single emission
                # could be implemented in the addLineCut function?
                while self.spinBox_ROI.value() > len(self.lineCuts):
                    self.addLineCut()
            elif self.comboBox_ROI.currentText() == 'ROI':
                # the while is necessary, because the sigValueChanged may combine fast changes to a single emission
                # could be implemented in the addROI function?
                while self.spinBox_ROI.value() > len(self.ROIs):
                    self.addROI()
        else:
            if self.comboBox_ROI.currentText() == 'Line cut':
                # print('removeLineCuts called without every!')
                while self.spinBox_ROI.value() < len(self.lineCuts):
                    self.removeLineCut()
            elif self.comboBox_ROI.currentText() == 'ROI':
                while self.spinBox_ROI.value() < len(self.ROIs):
                    self.removeROI()



###################################



    def updateImage(self):
        autoscale = self.checkBox_autoColor.isChecked()
        background = (self.checkBox_subtract.isChecked(), self.checkBox_divide.isChecked())

        below, above = None, None
        if self.checkBox_maskBelow.isChecked():
            below = self.doubleSpinBox_maskBelow.value()
        if self.checkBox_maskAbove.isChecked():
            above = self.doubleSpinBox_maskAbove.value()
        mask = (below, above)
        tr = self.comboBox_transform.currentText()
        filt = self.comboBox_filter.currentText()

        imRange = self.horizontalSlider.value()
        #imRange = self.dataDict['']
        if self.checkBox_fullStack.isChecked():
            imRange = (0, 'Inf')
        self.imageDataSet.getPlotData(imRange=imRange, background=background, mask=mask, transformation=tr, filt=filt)


        self.showData = self.imageDataSet.plotData

        self.img.setImage(self.showData, autoLevels=autoscale)
        self.img.show()

    def reportMemory(self, memoryThis, memoryPerc, cpuPerc):
        #self.statusBar().showMessage('PID: %s; %.1f MB; free mem: %.1f%%;  cpu %.1f' % (self.PID, memoryThis, 100-memoryPerc, cpuPerc))
        mem = memoryThis
        memunit='MB'
        if memoryThis > 1000:
            mem = memoryThis/1000.
            memunit = 'GB'
        self.statusUsageLabel.setText('PID: %s; %.1f %s; free mem: %.1f%%;  cpu %.1f%%' %
                                      (self.PID, mem, memunit, 100-memoryPerc, cpuPerc))

    def reportMemory2(self, text):
        self.statusUsageLabel.setText(text)


    def leaveProgram(self):
        print('bye')
        self.close()



def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

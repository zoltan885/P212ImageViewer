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

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
import psutil, time
import numpy as np
import os
import glob
import fabio

class MemoryMonitorClass(QObject):
    '''
    Class to monitor memory and cpu usage
    '''
    memorySignal = pyqtSignal(float, float, float)
    usageSignal = pyqtSignal(str)
    #def __init__(self):
    #    super().__init__()

    def run(self):
        while True:
            process = psutil.Process(os.getpid())
            memoryThis0 = process.memory_info().rss/1024./1024.
            memoryPerc = psutil.virtual_memory().percent
            cpuPerc = psutil.cpu_percent()
            memunit='MB'
            if memoryThis0 > 1000:
                memoryThis0 = memoryThis0/1000.
                memunit = 'GB'
            label = 'PID: %d;  %.1f %s;  free mem: %.1f%%;  cpu: %3.1f%%' % \
                (os.getpid(), memoryThis0, memunit, 100-memoryPerc, cpuPerc)
            self.usageSignal.emit(label)
            #self.memorySignal.emit(memoryThis0, memoryPerc, cpuPerc)
            time.sleep(1)


# class DataLoadClass(QObject):
#     '''
#     Class to load data in a separate thread
#     '''
#     dataLoadSignal = pyqtSignal(int)
#     dataLoadStartSignal = pyqtSignal()
#     dataLoadFinishedSignal = pyqtSignal()
#     #def __init__(self):
#     #    super().__init__()

#     def run(self):
#         self.dataLoadStartSignal.emit()
#         steps = 100
#         for i in range(steps):
#             self.dataLoadSignal.emit(100*i/steps)
#             time.sleep(0.02)
#         self.dataLoadFinishedSignal.emit()





class DataLoadSignals(QObject):
    '''
    worker thread signals: This class is needed because the ThreadPool
    needs a class inherited from QRunnable, but that does not support signals and slots
    started: none
    finished: none
    error: tuple (exctype, value, traceback.format_exc() )
    result: object data returned from processing, anything
    progress: int indicating % progress
    '''
    started = pyqtSignal(bool)   # in principle no type should be defined, but then it does not work
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    names = pyqtSignal(str, object)  # setName, filenames-list
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class DataGenerateClass(QRunnable):
    '''
    Class to generate data in a QThreadPool
    '''
    def __init__(self, *args, **kwargs):
        super().__init__()
        #self.data = data
        #self.size = size
        self.args = args
        self.kwargs = kwargs
        self.size = self.kwargs['size']
        self.signals = DataLoadSignals()

        #self.kwargs['progress'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        bunch = 10
        noBunch = self.size//bunch  # only generates multiples of bunch, but this is only a test function
        self.signals.started.emit()
        for s in range(noBunch):
            d = np.random.rand(bunch, 600, 400)
            for i,im in enumerate(d):
                d[i] = im + (i+s*bunch)/5.
                self.signals.progress.emit(int(100*(s*bunch+(i+1))/(noBunch*bunch)))
                #time.sleep(0.1)
            self.signals.result.emit(d)
            #time.sleep(1)

        self.signals.finished.emit()


class loadFolderClass(QRunnable):
    '''
    load an entire folder
    '''
    def __init__(self, path, slicing=None, chunkSize=5, *args, **kwargs):
        super().__init__()
        self.loadPath = path
        self.chunkSize = chunkSize
        self.multiTypes = ['cbf', 'tif']
        self.slicing = slicing
        self.nameOfSet = ''
        self.names = []
        self.signals = DataLoadSignals()
        print('Data load signals added to loadFolderClass')


    @pyqtSlot()
    def run(self):
        assert os.path.exists(self.loadPath), '%s does not exist' % self.loadPath
        assert os.path.isdir(self.loadPath), '%s is not a directory' % self.loadPath
        files = {}
        for t in self.multiTypes:
            files[t] = np.sort(glob.glob(self.loadPath+'/*.%s' % t))
            if len(files[t]) < 1:
                del files[t]
        assert len(files.keys()) < 2, 'There are different file types in folder %s' % self.loadPath
        assert len(files.keys()) > 0, 'There are no known type (%s) files in folder %s' % self.loadPath
        assert list(files.keys())[0] in ['cbf', 'tif'], 'Can only load an entire folder with either cbf or tif files.'
        if self.slicing is not None:
            try:
                self.files = eval('files[%s]' % self.slicing)
            except ValueError:
                print('Slicing not understood')
        else:
            self.files = files[list(files.keys())[0]]  # self.files should be a simple list of a single file type

        self.nameOfSet = self.loadPath.rpartition('/')[2]
        self.names = [f.rpartition("/")[2] for f in files]
        self.signals.names.emit(self.nameOfSet, self.names)

        self.signals.started.emit(True)
        print('Folder loading started')
        # noFullChunks = len(self.files)//self.chunkSize
        # restChunk = len(self.files)%self.chunkSize

        xSize, ySize = fabio.open(self.files[0]).data.shape
        dataChunk = np.zeros([self.chunkSize, xSize, ySize])
        print('So far so good...')
        for i, fn in enumerate(self.files):
            # EMIT FULL CHUNKS
            if i % self.chunkSize == 0:
                if i > 0:
                    print('emitting full chunk!')
                    self.signals.result.emit(dataChunk)
                    dataChunk = np.zeros([self.chunkSize, xSize, ySize])  # this is not needed; just for testing
            # EMIT THE LAST FRACTIONAL CHUNK
            if i == len(self.files)-1:
                rest = len(self.files) % self.chunkSize
                if rest == 0:
                    continue
                dataChunk = dataChunk[:rest]
                print('emitting rest (%i) chunk!' % rest)
                self.signals.result.emit(dataChunk)
            print('Adding data: %i' % i)
            dataChunk[i % self.chunkSize, :, :] = np.flipud(fabio.open(fn).data).astype('int32')
            self.signals.progress.emit(int(100*(i/len(self.files))))
        self.signals.finished.emit()


class CustomSignals(QObject):
    '''
    signals to emit
    '''
    chunkLoaded = pyqtSignal()


class ImageData():
    '''
    attr data: 3D data stack
    attr plotData: 2D data to plot
    '''
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.data = np.random.rand(1, 73, 73)
        self.plotData = self.data[0]
        if 'name' in self.kwargs.keys():
            self.setName = kwargs['name']
        else:
            self.setName = 'dataset_' + str(np.random.randint(1e5, 1e6))
        self.dataGenerate = DataGenerateClass(size=110)  # this has to be stared later
        self.dataFolderLoad = loadFolderClass('/home/zoltan/Documents/code_snippets/multisource/PEt')

        self.subtract = np.ones((600,400))
        self.subtract[:100, :100] = 2
        self.divide = np.ones((600,400))
        self.divide[150:300, 250:300] = 2

        self.signals = CustomSignals()


    def generate(self):
        '''
        test function to load data with QThreadPool
        this has to be exchanged to a load function!
        '''
        self.dataGenerate = DataGenerateClass(size=110)
        self.threadpool = QThreadPool()
        self.dataGenerate.signals.result.connect(self._loadChunk)
        self.threadpool.start(self.dataGenerate)

    def loadFolder(self):
        '''
        load an entire folder
        '''
        #self.dataFolderLoad = loadFolderClass('/home/zoltan/Documents/code_snippets/multisource/PEt/')
        self.threadpool = QThreadPool()
        self.dataFolderLoad.signals.result.connect(self._loadChunk)
        self.dataFolderLoad.signals.names.connect(self._getNames)
        self.threadpool.start(self.dataFolderLoad)

    def _getNames(self, setName, fileNames):
        self.setName = setName
        self.names = fileNames
        print('dataset name: %s' % self.setName)

    def _loadChunk(self, dataToBeAdded):
        '''
        gradual data loading helper function
        '''
        if self.data.shape == (1, 73, 73):
            self.data = dataToBeAdded
        else:
            assert self.data.shape[1:] == dataToBeAdded.shape[1:], "Different image sizes; cannot stack"
            self.data = np.concatenate((self.data, dataToBeAdded))
        self.signals.chunkLoaded.emit()

    def loadSubstractBg(self):
        pass

    def loadDivideBg(self):
        pass

    def _transform(self, tr):
        assert tr in ['flipUD', 'flipLR', 'rot90', 'rot180', 'rot270', 'transpose', 'rot180+tr'], "Unknown transformation"
        if tr == 'flipUD':
            self.plotData = np.flipud(self.plotData)
        elif tr == 'flipLR':
            self.plotData = np.fliplr(self.plotData)
        elif tr == 'rot90':
            self.plotData = np.rot90(self.plotData, k=1)
        elif tr == 'rot180':
            self.plotData = np.rot90(self.plotData, k=2)
        elif tr == 'rot270':
            self.plotData = np.rot90(self.plotData, k=3)
        elif tr == 'transpose':
            self.plotData = np.transpose(self.plotData)
        elif tr == 'rot180+tr':
            self.plotData = np.rot90(np.transpose(self.plotData), k=2)

    def getPlotData(self, imRange=None, filt='mean', background=None, mask=None, transformation=None):
        '''
        function to prepare the plot data
        imRange should be a tuple: (min, max)
        background should be a boolean tuple: (subtract, divide)
        mask should be a float tuple (maskBelow, maskAbove)
        '''
        assert hasattr(self, 'data'), "No data loaded yet"
        # GETTING IMAGE OR FILTERED IMAGE RANGE
        if len(imRange) == 1:  # this is when there is no range
            self.plotData = self.data[imRange[0]].copy()  # otherwise it is just a reference; original data would be changed
        else:
            start = imRange[0]
            finish = imRange[1]
            if imRange[1] == 'Inf':
                start = 0
                finish = self.data.shape[0]
                # print('Filtering %d --> %d' % (start, finish))
            if filt == 'mean':
                self.plotData = np.mean(self.data[start:finish], axis=0)
            elif filt == 'max':
                self.plotData = np.maximum.reduce(self.data[start:finish], axis=0)

        # BACKGROUND CORRECTION
        if background[0] and background[1]:
            try:
                divider = self.divide-self.subtract
                divider[abs(divider)<1e-6] = 0.1
                self.plotData = (self.plotData-self.subtract / divider)
            except ValueError:
                print('Division with zero!')
        elif background[0] and not background[1]:
            self.plotData = self.plotData-self.subtract
        elif not background[0] and background[1]:
            try:
                self.divide[abs(self.divide)<1e-6] = 0.1
                self.plotData = self.plotData / self.divide
            except ValueError:
                print('Division with zero!')

        # MASKING
        if mask is not None:
            if mask[0] is not None:
                self.plotData[self.plotData < mask[0]] = mask[0]
            if mask[1] is not None:
                self.plotData[self.plotData > mask[1]] = mask[1]

        # IMAGE TRANSFORMATIONS
        if transformation not in ['None', 'none']:
            self._transform(transformation)







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


'''
QThread vs. QRunnable
https://www.toptal.com/qt/qt-multithreading-c-plus-plus
https://realpython.com/python-pyqt-qthread/

Handling large datasets
https://pythonspeed.com/articles/mmap-vs-zarr-hdf5/

speeding things up
https://pythonspeed.com/datascience/#memory

'''


from PyQt5.QtCore import QObject, pyqtSignal, QThread
import psutil, time
import numpy as np
import os
import glob
import fabio


class generateData(QObject):
    started = pyqtSignal()
    sizesignal = pyqtSignal(int)
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    result = pyqtSignal(object)

    size = 110

    def run(self):
        bunch = 10
        noBunch = self.size//bunch
        self.started.emit()
        print('start signal emitted')
        for s in range(noBunch):
            d = np.random.rand(bunch, 600, 400) + 100
            for i,im in enumerate(d):
                d[i] = im + (i+s*bunch)/5.
                self.progress.emit(int(100*(s*bunch+(i+1))/(noBunch*bunch)))
                #time.sleep(0.1)
                if i%10==0:
                    print('progress signal emitted: %.2f' % int(100*(s*bunch+(i+1))/(noBunch*bunch)))
            self.result.emit(d)
        self.sizesignal.emit(self.size)   # TODO
        self.finished.emit()



class dataSet():
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.fullSet = None
        self.plotData = None


        # If this is here, then we can not generate several times... but that may not be necessary
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.generator = generateData() # this has to be in the init, bacause otherwise
                                        # it would not exist when the signals are connected
        # Step 4: Move worker to the thread
        self.generator.moveToThread(self.thread)

    def generate(self):

        # Step 5: Connect signals and slots
        self.thread.started.connect(self.generator.run)
        self.generator.result.connect(self._updateFullSet)
        self.generator.finished.connect(self.thread.quit)
        self.generator.finished.connect(self.generator.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Step 6: Start the thread
        self.thread.start()

    def _updateFullSet(self, newData):
        print('Updating full dataset, size of new data: %s' % str(newData.shape))
        if self.fullSet is None:
            print('Was NONE')
            self.fullSet = np.array(newData)
        else:
            self.fullSet = np.append(self.fullSet, newData, axis=0)
            print("Appended: new size %s" % str(self.fullSet.shape))
        self._updatePlotData(0)

    def _updatePlotData(self, idx):
        if isinstance(idx, tuple):
            if idx[0] != idx[1]:
                print('Range seems to be enabled')
            else:
                try:
                    print('Updating: %d (set size: %d)' % (idx[0], self.fullSet.shape[0]))
                    self.plotData = self.fullSet[idx[0]]
                except:
                    pass
        elif isinstance(idx, int):
            self.plotData = self.fullSet[idx]


class dataSet2():
    '''
    This class holds an image set and the corresponding methods
    It is intendted for use outside the image viewer program
    '''
    def __init__(self, *args, **kwargs):
        pass


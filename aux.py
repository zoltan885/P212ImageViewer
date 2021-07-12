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

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
import psutil, resource, time
import numpy as np

class MemoryMonitorClass(QObject):
    memorySignal = pyqtSignal(float, float, float)
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            memoryThis = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024
            memoryPerc = psutil.virtual_memory().percent
            cpuPerc = psutil.cpu_percent()
            self.memorySignal.emit(memoryThis, memoryPerc, cpuPerc)
            time.sleep(0.5)


class DataLoadClass(QObject):
    dataLoadSignal = pyqtSignal(int)
    dataLoadStartSignal = pyqtSignal()
    dataLoadFinishedSignal = pyqtSignal()
    def __init__(self):
        super().__init__()

    def run(self):
        self.dataLoadStartSignal.emit()
        steps = 100
        for i in range(steps):
            self.dataLoadSignal.emit(100*i/steps)
            time.sleep(0.02)
        self.dataLoadFinishedSignal.emit()


class CustomSignals(QObject):
    '''
    worker thread signals: This class is needed because the ThreadPool 
    needs a class inherited from QRunnable, but that does not support signals and slots
    started: none
    finished: none
    error: tuple (exctype, value, traceback.format_exc() )
    result: object data returned from processing, anything
    progress: int indicating % progress
    '''
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)




class DataGenerateClass(QRunnable):
    def __init__(self, *args, **kwargs):
        super().__init__()
        #self.data = data
        #self.size = size
        self.args = args
        self.kwargs = kwargs
        self.size = self.kwargs['size']
        self.signals = CustomSignals()

        #self.kwargs['progress'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        bunch = 10
        noBunch = self.size//bunch
        self.signals.started.emit()
        for s in range(noBunch):
            d = np.random.rand(bunch, 500, 500)
            for i,im in enumerate(d):
                d[i] = im + i+s*bunch
                self.signals.progress.emit(int(100*(s*bunch+(i+1))/(noBunch*bunch)))
                time.sleep(0.01)
            self.signals.result.emit(d)
            time.sleep(0.2)

        self.signals.finished.emit()


class multiMax():
    def __init__(self, data):
        pass

















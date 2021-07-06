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

from scipy import interpolate, stats

import numpy as np
import fabio
import psutil
import scipy.ndimage
#from numba import jit
import time

from settings import *



class dataClass():
    def __init__(self, *args):
        self.data = np.zeros((500, 500))
        self.singleTypesFabio = ['cbf', 'tif']
        self.singleTypesHDF = ['h5', 'hdf', 'nexus']
        self.multiTypes = ['cbf', 'tif']
        self.eigerDataPath = EIGER2DP
        # here the config would need to be loaded, so that e.g. the default place for data in a nexus file is known

    def loadFile(self, path=None):
        '''
        load a single file

        '''

        if not os.path.exists(path):
            raise OSError('%s does not exist' % path)
            return
        if os.path.isfile(path):
            if path.rpartition('.')[2] in self.singleTypesFabio:
                self.data = np.flipud(fabio.open(path).data)
            elif path.rpartition('.')[2] in self.singleTypesHDF:
                try:
                    import h5py
                except ImportError('Could not import h5py. No hdf support available'):
                    return
                f = h5py.File(path, 'r')
                if self.hdfPath is not None:
                    # check if key exists!!!
                    self.data = f[self.hdfPath]
        else:
            raise IOError('%s is not a readable file' % path)
            return
        self.files = path


    def loadFolder(self, path=None, slicing=None, callback=None):
        '''
        path: a folder with a single type of images to load
        slicing: python type array slicing
        callback: function to update the progess bar while loading the files
        '''
        if not os.path.exists(path):
            raise OSError('%s does not exist' % path)
            return
        if not os.path.isdir(path):
            raise IOError('%s is not a directory' % path)
            return
        files = {}
        for t in self.multiTypes:
            files[t] = np.sort(glob.glob(path+'/*.%s' % t))
            if len(files[t]) < 1:
                del files[t]
        if len(files.keys()) > 1:
            raise IOError('There are different file types in folder %s' % path)
            return
        elif len(files.keys()) < 1:
            raise IOError('There are no known type (%s) files in folder %s' % (self.multiTypes, path))
            return
        else:
            if list(files.keys())[0] not in ['cbf', 'tif']:
                raise IOError('Can only load an entire folder with either cbf or tif files.')
                return
            files = files[list(files.keys())[0]]  # from here on files should be a simple list of a single file type
            if slicing is not None:
                try:
                    files = eval('files[%s]' % slicing)
                except ValueError:
                    print('Slicing not understood')
            xSize, ySize = fabio.open(files[0]).data.shape
            self.data = np.zeros([len(files), xSize, ySize])
            for i, fn in enumerate(files):
                if callback is not None:
                    callback(float(i+1)/len(files))
                self.data[i, :, :] = np.flipud(fabio.open(fn).data)
        self.steps = 1
        if slicing is not None:
            self.steps = int(slicing.rpartition(':')[2])
        self.files = files


    def loadEiger2(self, fname=None, slicing=None, frno=None, callback=None):
        '''
        Load Eiger2 hdf files
        This currently loads the full dataset to memory
        '''
        try:
            import h5py
        except ImportError('Could not import h5py. No hdf support available'):
            return 1
        f = h5py.File(fname, 'r')
        noIms = 0
        imShape = ()
        images = []

        self.E2Mask = np.array(f['entry/instrument/detector/detectorSpecific/pixel_mask'])
        # mask1 = np.where(self.E2Mask > 1)
        # mask2 = np.where(self.E2Mask == 1)

        for k in f[self.eigerDataPath].keys():  # should there be more than one datafile
            path = self.eigerDataPath + k
            noIms += f[path].shape[0]
            for i in range(noIms):
                images.append((self.eigerDataPath+k, i))
            imShape = f[path].shape[1:]
        #print(imShape)
        if slicing is not None:
            try:
                images = eval('images[%s]' % slicing)
            except ValueError:
                print('Slicing not understood')
        self.data = np.zeros([len(images), imShape[0], imShape[1]])
        for i, img in enumerate(images):
            if callback is not None:
                callback(float(i+1)/len(images))
            self.data[i, :, :] = np.flipud(f[img[0]][img[1]]).astype('int32')
        self.steps = 1
        if slicing is not None:
            self.steps = int(slicing.rpartition(':')[2])
        self.files = ['%s#%s' % (fi.rpartition('/')[2], fr) for (fi, fr) in images]


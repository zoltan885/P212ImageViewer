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





    def loadImage(self):
        self.Images = QFileDialog.getOpenFileNames(self, "Open file", baseFolder, "Image Files (*.cbf *.tif)")[0]
        self.Images = []
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
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", baseFolder, QFileDialog.ShowDirsOnly)
        self.Images = []
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
        self.p.param('Data Processing', 'imageNo').setOpts(limits=(0, len(self.Images)-1))
        self.updateRegion()

    def loadFolderMapped(self):
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", baseFolder, QFileDialog.ShowDirsOnly)
        self.Images = []
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
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", baseFolder, QFileDialog.ShowDirsOnly)
        self.Images = []
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
        self.dir = QFileDialog.getExistingDirectory(self, "Select a folder to load", baseFolder, QFileDialog.ShowDirsOnly)
        self.Images = []

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
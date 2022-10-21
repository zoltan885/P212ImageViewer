#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  1 14:46:00 2022

@author: hegedues

Eventually use this project for advanced docking:
    https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System
    perhaps needs to be built???
    python bindings seem a bit shaky


"""

from PyQt5 import QtWidgets, uic, Qt
from PyQt5.QtWidgets import QMenu


class renameDialog(QtWidgets.QDialog):
    # https://www.pythonguis.com/tutorials/pyqt-dialogs/
    def __init__(self, *args, **kwargs):
        super().__init__()
        uic.loadUi('renameDialog.ui', self)
        self.rejected.connect(self._delText)
        self.accepted.connect(self._updateText)

    def _updateText(self):
        # this is apparently necessary, becasue otherwise the lineEdit.text is a bult in method ?? WTF
        print('accepted')
        self.lineEdit.text = self.lineEdit.text()

    def _delText(self):
        print('rejected')
        self.lineEdit.text = ''



class tabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        # setup QTabWidget properties
        self.setTabsClosable(True)
        self.setTabBarAutoHide(True)
        self.setMovable(True)
        self.clear()

        self.tabs = []
        self.nextTabIdx = 0  # this makes sure that the tab number always increments
                             # just counting the current tabs would not do the trick
        self._addTab('tab_0')
        self.tabCloseRequested.connect(self._deleteTab)
        self.tabBarDoubleClicked.connect(self._renameTab)


    def _contextMenuEvent(self, event):
        # without the underscore it overwrites the default and shows the context menu, but not only for the menubar
        cm = QMenu(self.tabBar())
        detach = cm.addAction('detach')
        close = cm.addAction('close')
        action = cm.exec_(event.globalPos())
        if action == detach:
            print('Detaching tab')
        if action == close:
            print('Closing tab from context menu')

    def _renameTab(self, ind):
        print(ind)
        dlg = renameDialog()
        dlg.lineEdit.setText(self.tabText(ind))
        dlg.exec_()
        newname = dlg.lineEdit.text
        if newname != '':
            # check whether this name already exists
            namesInUse = [self.tabText(i) for i in range(len(self.tabs))]
            if newname in namesInUse:
                print('This name is already in use')
            else:
                ind = self.currentIndex()
                self.setTabText(ind, newname)
        print(newname)



    def _addTab(self, name):
        tC = tabContent()
        self.tabs.append(tC)
        _ = str(self.addTab(tC, name))  # returns the index of the tab
        self.nextTabIdx += 1

    def _deleteTab(self, ind):
        tabWidget = self.widget(ind)
        #print('Deleting tab %d: %s' % (ind, str(tabWidget)))
        self.removeTab(ind)
        self.tabs = [t for t in self.tabs if t != tabWidget]




class tabContent(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        uic.loadUi('tabWidget.ui', self)
        # self._disable_all()
        self.scrollAreaContainer.hide()
        self.toolbarVisible = False
        self._disableAll()
        # donno:
        if 'name' in list(kwargs.keys()):
            self.name = kwargs['name']

        self.sliderMax = 20
        self.sliderTickDist = 1
        self.plotArea.rangeSlider.useRange = False
        self.plotArea.rangeSlider.first_position = 0
        self.plotArea.rangeSlider.second_position = 0
        self.imgRange = (0, 0)

        self.plotArea.rangeSlider.update()

        # signals
        self.checkBox_useRange.stateChanged.connect(self._enableRange)

        self.plotArea.rangeSlider.signals.valuesChanged.connect(self.sliderChanged)
        self.spinBox_rangeStart.editingFinished.connect(self.updateSlider)
        self.spinBox_rangeStart.editingFinished.connect(self._updUpperLimit)
        self.spinBox_rangeFinish.editingFinished.connect(self.updateSlider)
        self.spinBox_rangeFinish.editingFinished.connect(self._updLowerLimit)
        self.checkBox_fullStack.stateChanged.connect(self.fullStack)
        self.updateSlider()

        self.plotArea.data.generator.sizesignal.connect(self._enableUponDataPresent)

        self.pushButton_scaleTranslate.clicked.connect(self.plotArea._transform)




    def VC(self, tu):
        print(tu)

    def showImageToolbar(self):
        if self.toolbarVisible:
            self.scrollAreaContainer.hide()
            self.toolbarVisible = False
            print('hiding toolbar')
        else:
            self.scrollAreaContainer.show()
            self.toolbarVisible = True
            print('showing toolbar')


    def _disableAll(self):
        # Image
        self.label_transformation.setEnabled(False)
        self.comboBox_transform.setEnabled(False)
        self.checkBox_maskBelow.setEnabled(False)
        self.doubleSpinBox_maskBelow.setEnabled(False)
        self.checkBox_maskAbove.setEnabled(False)
        self.doubleSpinBox_maskAbove.setEnabled(False)
        self.checkBox_autoColor.setEnabled(False)
        self.checkBox_fixAspect.setEnabled(False)

        # Background
        self.checkBox_subtract.setEnabled(False)
        self.toolButton_subtract.setEnabled(False)
        self.checkBox_divide.setEnabled(False)
        self.toolButton_divide.setEnabled(False)

        # Range
        self.checkBox_useRange.setEnabled(False)
        self.checkBox_fullStack.setEnabled(False)
        self.label_rangeStart.setText('Image no')
        self.label_rangeStart.setEnabled(False)
        self.spinBox_rangeStart.setEnabled(False)
        self.label_rangeFinish.hide()
        self.spinBox_rangeFinish.setEnabled(False)
        self.label_rangeFilter.setEnabled(False)
        self.comboBox_filter.setEnabled(False)

        # Line plots
        self.scrollArea_2.setEnabled(False)

        self.label_linePlots.setEnabled(False)
        self.comboBox_ROI.setEnabled(False)
        self.spinBox_ROI.setEnabled(False)



    def _enableUponDataPresent(self, size):
        print('Data geneartion finished. Data set size: %d' % size)
        self.showImageToolbar()
        self.sliderMax = size
        if size > 200:
            self.sliderTickDist = 10
        elif size > 100:
            self.sliderTickDist = 5
        elif size > 50:
            self.sliderTickDist = 2
        print('Slider tick dist: %d' % self.sliderTickDist)
        self.updateSlider()
        # Image
        self.label_transformation.setEnabled(True)
        self.comboBox_transform.setEnabled(True)
        self.checkBox_maskBelow.setEnabled(True)
        self.doubleSpinBox_maskBelow.setEnabled(True)
        self.checkBox_maskAbove.setEnabled(True)
        self.doubleSpinBox_maskAbove.setEnabled(True)
        self.checkBox_autoColor.setEnabled(True)
        self.checkBox_fixAspect.setEnabled(True)

        # Background
        self.checkBox_subtract.setEnabled(True)
        self.toolButton_subtract.setEnabled(True)
        self.checkBox_divide.setEnabled(True)
        self.toolButton_divide.setEnabled(True)

        # Range
        self.checkBox_useRange.setEnabled(True)
        self.checkBox_useRange.setChecked(False)
        self.checkBox_fullStack.setEnabled(True)
        self.checkBox_fullStack.setChecked(False)
        self.label_rangeStart.setText('Image no')
        self.label_rangeStart.setEnabled(True)
        self.spinBox_rangeStart.setEnabled(True)
        self.label_rangeFinish.hide()
        self.spinBox_rangeFinish.setEnabled(False)
        self.label_rangeFilter.setEnabled(False)
        self.comboBox_filter.setEnabled(False)
        self.plotArea.rangeSlider.setRangeLimit(0, self.sliderMax)

        # Line plots
        self.scrollArea_2.setEnabled(False)

        self.label_linePlots.setEnabled(False)
        self.comboBox_ROI.setEnabled(False)
        self.spinBox_ROI.setEnabled(False)


    def _enableRange(self):
        if self.checkBox_useRange.isChecked():
            self.label_rangeFilter.setEnabled(True)
            self.comboBox_filter.setEnabled(True)
            self.label_rangeStart.setText('From')
            self.label_rangeFinish.show()
            self.spinBox_rangeStart.setEnabled(True)
            self.spinBox_rangeFinish.setEnabled(True)
            self.checkBox_fullStack.setEnabled(True)

            self.plotArea.rangeSlider.setRangeLimit(0, self.sliderMax)
            self.plotArea.rangeSlider.useRange = True


            #currImNo = self.horizontalSlider.value()[0]
            #self.horizontalSlider.setValue((currImNo-3, currImNo+3))
            #self.horizontalSlider.LabelPosition.LabelsAbove
        else:
            self.label_rangeFilter.setEnabled(False)
            self.comboBox_filter.setEnabled(False)
            self.label_rangeStart.setText('Image no')
            self.label_rangeFinish.hide()
            self.spinBox_rangeFinish.setEnabled(False)
            self.spinBox_rangeFinish.setValue(0)
            self.checkBox_fullStack.setChecked(False)  # this calls the self.fullStackFilter; stuff gets enabled


            self.plotArea.rangeSlider.useRange = False
            avg = int((self.plotArea.rangeSlider.second_position+
                       self.plotArea.rangeSlider.first_position)/2)
            self.plotArea.rangeSlider.second_position = avg
            self.plotArea.rangeSlider.first_position = avg
            self.spinBox_rangeStart.setValue(avg)
            self.plotArea.rangeSlider.update()



            #currImNo = (self.horizontalSlider.value()[0] +
            #            self.horizontalSlider.value()[1]) //2
            #self.horizontalSlider.setValue((currImNo,))

    def fullStack(self):  # needs some work!
        if self.checkBox_fullStack.isChecked():
            self.checkBox_useRange.setEnabled(False)
            self.spinBox_rangeStart.setEnabled(False)
            self.spinBox_rangeFinish.setEnabled(False)
            self.sliderChanged((0, self.sliderMax))
        else:
            self.checkBox_useRange.setEnabled(True)
            self.spinBox_rangeStart.setEnabled(True)
            self.spinBox_rangeFinish.setEnabled(True)
            self.sliderChanged(self.imgRange)

    def _updUpperLimit(self):
        if self.spinBox_rangeStart.value() > self.spinBox_rangeFinish.value():
            self.spinBox_rangeFinish.setValue(self.spinBox_rangeStart.value())
            self.updateSlider()

    def _updLowerLimit(self):
        if self.spinBox_rangeFinish.value() < self.spinBox_rangeStart.value():
            self.spinBox_rangeStart.setValue(self.spinBox_rangeFinish.value())
            self.updateSlider()


    def updateSlider(self):
        self.plotArea.rangeSlider.opt.maximum = self.sliderMax
        self.plotArea.rangeSlider.setTickInterval(self.sliderTickDist)
        if self.checkBox_useRange.isChecked():
            self.plotArea.rangeSlider.setRange(self.spinBox_rangeStart.value(),
                                               self.spinBox_rangeFinish.value())
            self.imgRange =(self.spinBox_rangeStart.value(),
                            self.spinBox_rangeFinish.value())
        else:
            self.plotArea.rangeSlider.setRange(self.spinBox_rangeStart.value(),
                                               self.spinBox_rangeStart.value())
            self.imgRange =(self.spinBox_rangeStart.value(),
                            self.spinBox_rangeStart.value())

    def sliderChanged(self, vals):
        #print('Slider: %s' % str(vals))
        self.spinBox_rangeStart.setValue(vals[0])
        if self.checkBox_useRange.isChecked():
            self.spinBox_rangeFinish.setValue(vals[1])
            self.imgRange = (vals[0], vals[1])
        else:
            self.spinBox_rangeFinish.setValue(0)
            self.imgRange = (vals[0], vals[0])
        self._updateImageRange()

    def _updateImageRange(self):
        self.plotArea.data._updatePlotData(self.imgRange)
        self.plotArea._updateImage()
        #self.ROIChanged()
        #self.lineCutsChanged()

        # enable on ticking the box
        #self.checkBox_useRange.stateChanged.connect(self.enableRange)
        #self.comboBox_filter.currentTextChanged.connect(self.updateImage)
        #self.checkBox_fullStack.stateChanged.connect(self.fullStackFilter)

        # # RANGE SLIDER
        # self.rs = self.tabWidget.currentWidget()
        # self.rs.rangeSlider.setMinimum(0)
        # self.rs.rangeSlider.setMaximum(1)  # this is kind of a placeholder
        # self.rs.rangeSlider.setValue(0)







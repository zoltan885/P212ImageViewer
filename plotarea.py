#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  1 10:12:31 2022

@author: hegedues
"""
from PyQt5 import QtWidgets, uic

class plotArea(QtWidgets.QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent)  # this is needed for the promotion
        uic.loadUi('plotAreaWidget.ui', self)
        print('Plot area created')

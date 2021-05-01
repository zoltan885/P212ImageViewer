#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  1 13:26:58 2021

@author: Hegedues
"""


def _fioReader(fiofile):
    with open(fiofile, 'r') as f:
        fiocontent = f.readlines()
    for l in fiocontent:
        if 'channel1_FileDir1' in l:
            folder = l.split('=')[1].strip()


    return folder

class fioDataset:
    '''
    the class represents a column of a FIO file. The first column is the
    x-axis which is used by all columns, name_in, e.g. test_00001_C1
    '''
    def __init__(self, name_in):
        self.name = name_in
        #print name_in
        lst = self.name.split('_')
        if len(lst) > 1:
            self.deviceName = lst[-1]
            if self.deviceName.find( "0") == 0:
                self.deviceName = "ScanName"
        else:
            if '/' in name_in:
                try:
                    self.deviceName = PT.AttributeProxy(name_in).get_config().label
                except:
                    self.deviceName = name_in
            else:                
                self.deviceName = name_in
                            
        self.x = []
        self.y = []
        return


def _read(name):
    comments = []
    user_comments = []
    parameters = []
    dataSets = []

    try:
        inp = open( name, 'r')
    except IOError as e:
        print("Failed to open {0}, {1}".format(name, e.strerror))
        sys.exit(255)
    lines = inp.readlines()
    inp.close()
    flagComment = 0
    flagParameter = 0
    flagData = 0
    for line in lines:
        line = line.strip()
        if line.find("!") == 0:
            user_comments.append(line)
            flagComment = False
            flagParameter = False
            flagData = False
        elif line.find("%c") == 0:
            flagComment = True
            flagParameter = False
            flagData = False
            continue
        elif line.find("%p") == 0:
            flagComment = False
            flagParameter = True
            flagData = False
            continue
        elif line.find("%d") == 0:
            flagComment = False
            flagParameter = False
            flagData = True
            continue
        #
        if flagComment:
            comments.append(line)
        #
        # parName = parValue
        #
        if flagParameter:
            lst = line.split("=")
            parameters.append({lst[0]: lst[1]})
        if not flagData:
            continue
        if 'none' in line.lower():
            continue
        lst = line.split()
        if lst[0] == "Col":
            #
            # the 'Col 1 ...' description does not create a
            # new FIO_dataset because it contains the x-axis for all
            #
            if lst[1] == "1":
                pass
            else:
                dataSets.append(fioDataset(lst[2]))
        else:
            for i in range(1, len(dataSets)+1):
                dataSets[i-1].x.append(lst[0])
                dataSets[i-1].y.append(lst[i])





    return dataSets, parameters

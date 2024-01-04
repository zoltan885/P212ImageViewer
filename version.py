#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2021-2023 Hegedues

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


NAME = 'P21.2 ImageViewer'
VERSION = {'major': 0, 'minor': 5, 'patch': 1}
YEAR = '2021 - 2024'

copyrightNotice = "\n\n    %s version %i.%i.%i\n    Copyright (C) Hegedues %s\n\
    This program comes with ABSOLUTELY NO WARRANTY; for details see the LICENSE."\
    % (NAME, VERSION['major'], VERSION['minor'], VERSION['patch'], YEAR)

#
changelog ={
    'version 0.4': [
        'Added Eiger2 hdf support'
        ],
    'version 0.4.1': [
        'Fixed deprecation warning from pyqtgraph',
        'Fixed single image load',
        'Fixed cursor hover value',
    ],


    }

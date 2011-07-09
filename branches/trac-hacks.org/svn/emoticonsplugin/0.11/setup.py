#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from setuptools import setup, find_packages

setup(
    name = 'TracEmoticons', version = '0.1',
    author = 'Christopher Lenz', author_email = 'cmlenz@gmx.de',
    url = 'http://trac-hacks.swapoff.org/wiki/EmoticonsPlugin',
    description = 'Emoticon support for Trac',
    license = 'GPL',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracemoticons': ['icons/*.*']
    },
    entry_points = {
        'trac.plugins': ['tracemoticons = tracemoticons']
    },
    zip_safe = False
)

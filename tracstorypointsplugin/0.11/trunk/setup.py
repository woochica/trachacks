'''
Setup and Configuration file.

    @author: scott turnbull <sturnbu@emory.edu>
    Copyright (C) 2010  Scott Turnbull

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from setuptools import find_packages, setup

setup(
    name='TracStorypoints', version='0.1',
    author = 'scott turnbull',
    author_email = 'sturnbu@emory.edu',
    url = 'https://techknowhow.library.emory.edu',
    description = 'A lightweight plugin for Trac story point tracking and code completion date',
    license = 'GPLv3',

    packages = ['tracstorypoints'],
    # package_data = {'tracstorypoints' : ['conf/*.ini']},
    entry_points = {'trac.plugins': 'tracstorypoints = tracstorypoints'},

    install_requires = ['Trac>=0.11'],
    keywords = 'trac agile estimation'
)

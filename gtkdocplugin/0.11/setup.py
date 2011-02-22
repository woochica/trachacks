# This file is part of TracGtkDoc.
# Copyright (C) 2011 Luis Saavedra <luis94855510@gmail.com>
#
# TracGtkDoc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TracGtkDoc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TracGtkDoc.  If not, see <http://www.gnu.org/licenses/>.
#
# $Author$
# $Date$
# $Revision$

from setuptools import setup

setup(
    name='TracGtkDoc',
    version='0.2.0',

    author='Luis Saavedra',
    author_email='luis94855510@gmail.com',

    url='http://trac-hacks.org/wiki/GtkDocPlugin',
    description='GtkDoc plugin for Trac',

    license = "GPLv3",

    zip_safe=True,
    packages=['tracgtkdoc'],
    package_data={'tracgtkdoc': [
        'templates/*.html',
    ]},

    install_requires = [
        #'trac>=0.11',
    ],

    entry_points={'trac.plugins': [
        'tracgtkdoc.admin = tracgtkdoc.admin',
        'tracgtkdoc.search = tracgtkdoc.search',
        'tracgtkdoc.web_ui = tracgtkdoc.web_ui',
    ]},

    keywords='trac gtkdoc',
)

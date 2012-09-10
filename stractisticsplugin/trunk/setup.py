# -*- coding: utf-8 -*-
#
# Stractistics
# Copyright (C) 2008 GMV SGI Team <http://www.gmv-sgi.es>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# $Id: setup.py 432 2008-07-11 12:58:49Z ddgb $
#
from setuptools import setup, find_packages

PACKAGE = 'STractistics'
VERSION = '0.5.0b'

setup(name=PACKAGE, 
      version=VERSION, 
      author='Daniel Gómez Brito, Manuel Jesús Recena Soto',
      author_email='dagomez@gmv.com, mjrecena@gmv.com',
      maintainer='Ryan J Ollos',
      maintainer_email='ryan.j.ollos@gmail.com',
      license='GNU GPL v2',
      description='Allows to gauge project activity at a glance. Developed by GMV Soluciones Globales Internet',
      url='http://trac-hacks.org/wiki/StractisticsPlugin',
      packages = ['stractistics'], 
      entry_points={'trac.plugins': ['%s = stractistics.web_ui' % PACKAGE ]},
      package_data={'stractistics': ['templates/*.html',
                                     'htdocs/css/*.css',
                                     'htdocs/images/*.jpg',
                                     'htdocs/swf/*.swf',
                                     'htdocs/javascript/*.js',                                     
                                     'htdocs/javascript/js-ofc-library/*.js',
                                     'htdocs/javascript/js-ofc-library/charts/*.js']} 
)

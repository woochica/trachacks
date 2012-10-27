# -*- coding: utf-8 -*-

import os

# http://docs.python.org/distutils/apiref.html
from setuptools import find_packages, setup

# define some names/files/pathes
pppackagedir = u'projectplan'
pppackage = 'projectplan'
templatesdir = u'templates'
htdocsdir = u'htdocs'
htdocsubdirmapping = { 
		       u'css': u'*.*',
		       u'images': u'*.*',
		       u'images/*': u'*.*',
		       u'images/*/*': u'*.*',
		       u'images/*/*/*': u'*.*',
		       u'js': u'*.js',
		       #u'js': u'jquery-tooltip/*.js',
		       u'js/jquery-tablesorter': u'*.*',
		       u'js/jquery-tooltip': u'*.*',
		       u'js/jquery-tooltip/lib': u'*.js',
		       u'js/jquery-burndown': u'*.*',
		        }
pptemplatesglob = [ os.path.join( templatesdir, u'*.html' ) ]
pphtdocsglob = [ os.path.join( htdocsdir, subdir, globmap )
		 for subdir, globmap in htdocsubdirmapping.items() ]
pppackagedataglobs = pphtdocsglob + pptemplatesglob

# create setup instance - done
setup(
  name = u'ProjectPlan',
  version = u'0.91.4',
  description = u'ProjectPlanPlugin for Trac',
  long_description = u"""
    ProjectPlan Plugin basicaly adds the possibility for fast and
    easy integration of different project mananagement visualizations
    (those working on the tickets and generating output like reports, charts and so on).
    The output generation does work in three steps:
      1. collect the tickets needed for the output: can be controlled by user arguments if its allowed by the output/plugin
      2. calculate (controlled by output), some calculations can be enabled/disabled with user arguments, depending on the output
      3. render (generate the output), controlled by user arguments, additional arguments are output dependend
    Additional information can be found at the Trac-Hacks Projectpage for this Plugin.
  """,
  author = u'anbo & makadev',
  author_email = u'makadev at googlemail dot com',
  url = u'http://trac-hacks.org/wiki/ProjectPlanPlugin',
  download_url = u'http://trac-hacks.org/svn/projectplanplugin',
  #packages = [ pppackage ],
  packages = find_packages(),
  license = u'GPL2',
  keywords = u'project plan visualization',
  #package_dir={ pppackage: pppackagedir , },
  package_data = { pppackage: pppackagedataglobs },
  install_requires = ( u'Trac >=0.11, <0.13' ),
  entry_points = { u'trac.plugins': u'projectplan = projectplan.projectplan' }
)

#!/usr/bin/env python
import sys
from setuptools import setup

min_python = (2, 5)
if sys.version_info < min_python:
    print "TimingAndEstimation requires Python %d.%d or later" % min_python
    sys.exit(1)
if sys.version_info >= (3,):
    print "TimingAndEstimation doesn't support Python 3 (yet)"
    sys.exit(1)


PACKAGE = 'timingandestimationplugin'

setup(name=PACKAGE,
      description='Plugin to make Trac support time estimation and tracking',
      keywords='trac plugin estimation timetracking',
      version='1.2.7',
      url='http://www.trac-hacks.org/wiki/TimingAndEstimationPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      This Trac 0.11 plugin provides support for Time estimation and tracking.

      See http://trac-hacks.org/wiki/TimingAndEstimationPlugin for details.
      """,
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.html', 'htdocs/*']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)})


#### AUTHORS ####
## Primary Author:
## Russell Tyndall
## Acceleration.net
## russ@acceleration.net
## trac-hacks user: bobbysmith007

##

## Alessio Massaro
## trac-hacks user: masariello
## Helped Get Reports working in postgres
## and started moving toward generic work
## rather than hours

## kkurzweil@lulu.com
## helped postegresql db backend compatiblity

## jonas
## made it so that base_url was unnecessary

## Colin Guthrie
## trac-hacks user: coling
## Refactored the custom reports code to make it
##  easy for other plugins to provide reports to
##  compliment those provided by default
## Added Javascript that improves Ticket UI

## Dave Abrahams <dave@boost-consulting.com>
##
## Genshi filters to remove T&E reports from the
## standard reports page, where they display errors

## Greg Troxel
##
## Updated the post commit hooks to be inline with upstream trac

## Tay Ray Chuan
##
## Added a stopwatch to the ticket pages

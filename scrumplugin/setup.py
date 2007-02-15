#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'scrumplugin'

setup(name=PACKAGE,
    description='Trac plugin to do basic project planning, tracking and charting',
    keywords='trac plugin project planning tracking chart timingandestimationplugin scrumburndownplugin',
    version='1.0.0',
    url='',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Alessio M.',
    author_email='amassaro@fastmail.fm',
    long_description="""
This plugin provides some basic project management essentials to do
Scrum-style iteration planning in an Agile project.

The plugin is a sort of Trac adaptation of the concepts in
[http://www.mountaingoatsoftware.com Agile Estimating and Planning by Mike Cohn]

The code itself is a radical merge&rework of TimingAndEstimationPlugin and
ScrumBurndownPlugin. The billing features in TimingAndEstimationPlugin have
not been implemented, and the !JavaScript charting features in ScrumBurndownPlugin
have been redone with a Java applet using [http://www.jfree.org/jfreechart JFreeCharts].
Also, the burndown chart has been changed into a burnup, and the the milestone
period is indicated by an interval marker.

The upgrade procedure creates a column called 'started' in the milestone table,
some SQL views and functions, and some Trac reports. No external scripts are needed
to collect iteration statistics. Everything is done with SQL queries.

The plugin needs two custom ticket fields, so the following must be added to the
trac.ini file of the environment:
{{{
[ticket-custom]
estimatedwork = text
estimatedwork.label = Estimated Work
estimatedwork.order = 1
estimatedwork.value = 0
workdone = text
workdone.label = Work done
workdone.order = 2
workdone.value = 0
}}}

Instead of entering some value that is then added to the workdone counter for a
specific ticket, users enter the actual new value. So if for a ticket the current
number of workdone hours (or whichever tracking unit you chose for your project)
is 7, and an engineer has just done 3 more hours, he should simply input 10 and
submit.

The iteration burnup chart simply groups all the tickets that currently belong
to the selected milestone, and starts plotting all changes to the the sums of
their work estimated and done values. The iteration period is marked by an
interval marker. If work has done on the tickets outside of the iteration period,
then some points will be plotted outside the marked area.
""",
    packages=[PACKAGE],
    package_data={PACKAGE : ['templates/*.cs', 'htdocs/*']},
    entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)}
)

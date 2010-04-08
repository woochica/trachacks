#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'jobcontrol'

setup(name=PACKAGE,
    description='A job scheduler and monitoring plug-in for Trac',
    keywords='trac plugin ticket cron jobcontrol scheduling monitoring',
    version='0.1',
    url='http://www.trac-hacks.org/wiki/JobControlPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Thanos Vassilakis',
    author_email='thanos@syntazo.com',
    long_description="""
    The plugin lets you set up and manage and monitor scheduled jobs. It adds the following new Admin screens to Trac: 
Job Admin - List and lets you add, edit and delete jobs. 
Job Status Map - Where you can see the status of the last run of all the jobs. From here you can drill down to the run view of a particular job. 
Run View - Lists all job runs, showing you the runs status form where you can drill down to the runs log. 
Log Admin - Clean-up logs and other tasks. 

Each job run environment and schedule is specified by the version of a single configuration file - a python script - in the SCM. Therefore any changes are carefully tracked. This script is used to create the sandbox and invoke the job.
    """,
    packages=[PACKAGE],
    package_data={PACKAGE : ['templates/*.html', 'htdocs/*.css']},
    entry_points = {
        'trac.plugins': [
            'jobcontrol.upgrade = jobcontrol.upgrade',
            'jobcontrol.job = jobcontrol.job',
            'jobcontrol.model = jobcontrol.model',
            'jobcontrol.admin = jobcontrol.admin',
        ]
    })

#### AUTHORS ####
## Primary Author:
## Thanos Vassilakis
## http://www.syntazo.com/
## thanos@syntazo.com
## trac-hacks user: thanos

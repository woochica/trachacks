# -*- encoding: UTF-8 -*-

'''
Created on 12 oct. 2010

@author: thierry
'''
import ez_setup
ez_setup.use_setuptools()

from setuptools import find_packages, setup

setup(
    name = 'TracCronPlugin',
    version = '0.1',
    package_dir = {'': 'src'},
    packages= find_packages('src'),
    package_data = { 'traccron': [ 'templates/*.*'] },
    author = "Thierry Bressure",
    author_email = 'thierry@bressure.net',
    maintainer = 'Thierry Bressure',
    maintainer_email = "thierry@bressure.net",
    description = "Trac task scheduler  plugin for Trac.",
    license = "BSD",
    url = "http://trac-hacks.org/wiki/TracCronPlugin",
    keywords = "trac cron schedeluer plugin",    
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [],
    entry_points = {'trac.plugins': [
                                     'core = traccron.core',
                                     'task = traccron.task',
                                     'scheduler = traccron.scheduler',
                                     'listener = traccron.listener',
                                     'history = traccron.history'
                                     ]},
)
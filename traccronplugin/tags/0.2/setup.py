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
    version = '0.2',
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
    keywords = "trac cron scheduler plugin",    
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [],
    entry_points = {'trac.plugins': [
                                     'traccron.core = traccron.core',
                                     'traccron.task = traccron.task',
                                     'traccron.scheduler = traccron.scheduler',
                                     'traccron.listener = traccron.listener',
                                     'traccron.history = traccron.history'
                                     ]},
)
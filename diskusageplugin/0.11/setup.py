# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name='DiskUsagePlugin', version='0.1',
    author = "lino",
    author_email = "",
    description = "This plugin visible trac and svn disk usage from admin panel",
    license = "BSD",
    url = "",
    packages=find_packages(exclude=['*.tests*']),
    package_data = {'diskusage': ['templates/*.html', ]},
    entry_points = {'trac.plugins': ['diskusage = diskusage']},
)

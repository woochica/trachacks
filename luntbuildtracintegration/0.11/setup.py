#!/usr/bin/python

from setuptools import find_packages, setup

setup(
    name='LuntbuildTracIntegration', version='1.1',
    author="David Roussel",
    description="A trac plugin to add Luntbuild builds to the trac timeline",
    packages=find_packages(exclude=['*.tests*']),
    package_data={'LuntbuildTracIntegration' : ['htdocs/*.css', 'htdocs/*.gif']},
    entry_points = """
[trac.plugins]
LuntbuildTracIntegration = LuntbuildTracIntegration.LuntbuildTracIntegrationPlugin
    """
)

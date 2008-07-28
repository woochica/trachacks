from setuptools import find_packages, setup

setup(name='TracCia',
      version='0.2',
      packages = find_packages(),
      entry_points="""
[trac.plugins]
traccia = traccia
"""
      )

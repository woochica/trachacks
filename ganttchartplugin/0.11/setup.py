#!/usr/bin/python
from os.path import isfile, join
import glob
import os
import re

from setuptools import setup


if isfile("MANIFEST"):
    os.unlink("MANIFEST")


VERSION = re.search('__version__ = "([^"]+)"',
                    open("gantt/__init__.py").read()).group(1)


setup(name="gantt",
      version = VERSION,
      description = "trac wiki plugin to render gantt charts",
      author = "Malcolm Smith",
      author_email = "malcolm@ripple6.com",
      url = "http://trac-hacks.org/wiki/GanttChartPlugin",
      license = "PSF License",
      long_description =
"""\
The ganttplugin module renders gantt charts in trac wiki
""",
      packages = ["gantt"],
      package_data={"": ["*.tar.bz2"]},
      include_package_data=True,
      entry_points={'trac.plugins': ['gantt=gantt']},
      install_requires = ['PyYAML', 
                          'python-dateutil',
                          'PIL']
      )

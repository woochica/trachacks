# -*- coding: utf-8 -*-
from setuptools import setup

version='0.0.1'

setup(name='CalendarPopUp',
      name = "CalendarPopUp",
      version=version,
      description="show selectable calendar pop-up where needed",
      author='Julian Dittrich',
      author_email='julian@nextwii.de',
      url='http://nextwii.de',
      keywords='trac plugin',
      license="GPL",
      packages = ['calendarpopup'],      
      include_package_data=True,
      package_data={'calendarpopup': ['htdocs/css/*', 'htdocs/js/*']},
      install_requires = [
        #'trac>=0.11',
      ],
      entry_points = {
        'trac.plugins': [
            'calendarpopup = calendarpopup',
        ]
      }
)


# -*- coding: utf-8 -*-
"""
Trac plugin that renders any 'README' files when browsing
directories in repository.

License: BSD
(c) 2009 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from setuptools import setup

setup(name='TracReposReadMePlugin',
      version='0.1',
      packages=['reposreadme'],
      author='CodeResort.com = BV Network AS',
      author_email='simon-code@bvnetwork.no',
      keywords='trac browser readme',
      description="Trac plugin that renders any 'README' files when browsing directories in repository.",
      url='http://www.coderesort.com',
      license='BSD',
      zip_safe = False,
      entry_points={'trac.plugins': [
            'reposreadme.reposreadme = reposreadme.reposreadme']},
      package_data={},
      install_requires = [])

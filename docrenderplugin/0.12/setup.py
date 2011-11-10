# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

version='0.2'

setup(name='docrender',
      version=version,
      description="Provide render for doc attachments",
      author='Boris Savelev',
      author_email='boris.savelev@gmail.com',
      url='http://trac-hacks.org/wiki/DocRenderPlugin',
      keywords='trac plugin doc pdf',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      entry_points = """
      [trac.plugins]
      docrender = docrender
      """,
      )

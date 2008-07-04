#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'DoapViewPlugin'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION,
      author = 'Rob Cakebread',
      maintainer = 'Rob Cakebread',
      author_email = 'cakebread@gmail.com',
      url='http://trac-hacks.org/wiki/DoapViewMacro',
      keywords='doap rdf trac foaf',
      long_description=open('README', 'r').read(),
      classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Framework :: Trac',
                 'Intended Audience :: Developers',
                 'Intended Audience :: End Users/Desktop',
                 'License :: OSI Approved :: BSD License',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 ],

      description='Renders DOAP (Description of a Project) RDF in a Trac wiki',
      license='GPL-2',
      package_dir={ 'DoapView' : 'DoapView'},
      packages=['DoapView'],
      package_data={ 'DoapView' : ['DoapView/*', 'DoapView/templates/*.html']},
      entry_points={'trac.plugins': ['DoapView.DoapView = DoapView.DoapView']},
      install_requires=['doapfiend']
)

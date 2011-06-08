#!/usr/bin/env python

# this code is entirely based on ShellExample by mOo <moolighttpd@gmail.com>
# located <http://xcache.lighttpd.net/wiki/ShellExample>
# but has been signifigantly updated


VERSION = '0.12.2'
PACKAGE = 'ShellExampleProcessor'
import os
from distutils.command.clean import clean as _clean
from setuptools import setup
from distutils.dir_util import remove_tree

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

class clean(_clean):

	def run(args):
		# run the base method
		_clean.run(args)
		remove_tree("build")
		remove_tree("dist")
		remove_tree("ShellExampleProcessor.egg-info")


setup(
		cmdclass = {'clean': clean},
		name = PACKAGE,
		version = VERSION,
		packages = ['shellexample'],
		package_data = { 'shellexample': [ '*.txt', 'htdocs/css/*.css'] },

		author = "mOo",
		author_email = 'moolighttpd@gmail.com',
		maintainer = 'Nathaniel Madura',
		maintainer_email = "nmadura@umich.edu",
		description = "shellexample plugin for Trac 0.12+",
		long_description=read(os.path.join("shellexample", "readme.txt")),
		license = "BSD",
		keywords = "trac shellexample wiki processor",
		url = "http://trac-hacks.org/wiki/ShellExampleMacro",
		classifiers = ['Framework :: Trac'],
		entry_points = {'trac.plugins': ['%s = shellexample.module' % PACKAGE]},
		)

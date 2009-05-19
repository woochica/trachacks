# $Id$

from setuptools import setup

PACKAGE = 'PreCodeBrowserPlugin'
VERSION = '1'
	
setup(
	name         = PACKAGE,
	version      = VERSION,
	url          = 'http://trac-hacks.org/wiki/%s' % PACKAGE,
	author       = 'Katherine Flavel',
	author_email = 'kate@elide.org',
	description  = 'Replace tables output in the source browser with simple <pre> file listings',

	license = 'Public Domain',
	install_requires = [ "Genshi >= 0.5dev" ],
	dependency_links = [ 'http://svn.edgewall.org/repos/genshi/trunk#egg = Genshi-0.5dev' ],

	packages = [ 'precodebrowser' ],

	entry_points = { 'trac.plugins': '%s = precodebrowser' % PACKAGE }
)


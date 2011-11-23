from setuptools import setup

VERSION = '0.1'
PACKAGE = 'sqlflexibleauthstore'

setup(
	name = 'SQLFlexibleAuthStorePlugin',
	version = VERSION,
	description = "Flexible SQL password store for Trac's AccountManager, including a store for permission groups and an admin page for them. This plugin was created by Dolf Andringa, but mainly shamefully stolen from the htgroup_editor and sqlauthstore plugins.",
	author = 'Dolf Andringa,Mitar,Chris Liechti',
	author_email = 'dolfandringa@gmail.com,mitar.trac@tnode.com,cliechti@gmx.net',
	url = '',
	keywords = 'trac plugin authentication sql group admin',
	license = 'GPLv3',
	packages = [PACKAGE],
    package_data={
        'sqlflexibleauthstore': [
            'templates/*.html',
            'sql/*.sql']
    },
	install_requires = [
		'TracAccountManager >= 0.3',
        'Genshi >= 0.5',
        'Trac >= 0.11'
	],
	zip_safe = False,
	entry_points = {
		'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE),
	},
)

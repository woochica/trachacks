from setuptools import setup

setup(
	name='privatereports',
	version='0.2',
	packages=['privatereports'],

	author='Michael Henke',
	author_email='michael.henke@she.net',
	description="A trac plugin that lets you control which groups and users can see a report",
	license="GPL",

	keywords='trac plugin security report group user',
	url='http://trac-hacks.org/wiki/PrivateReportsPlugin',
	
	classifiers = [
		'Framework :: Trac',
	],
	
	zip_safe=True,
	package_data=	{'privatereports': 
						[
							'templates/*.html'
						]
					},

	install_requires = ['Trac'],
	
	entry_points = {
		'trac.plugins': [
			'privatereports = privatereports',
		],
	},
)

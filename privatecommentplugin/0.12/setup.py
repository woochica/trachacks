from setuptools import setup

setup(
	name='privatecomments',
	version='0.3',
	packages=['privatecomments'],

	author='Michael Henke',
	author_email='michael.henke@she.net',
	description="A trac plugin that lets you create comments which are only visible for users with a special permission",
	license="GPL",

	keywords='trac plugin security ticket comment group',
	url='http://trac-hacks.org/wiki/PrivateCommentPlugin',
	
	classifiers = [
        'Framework :: Trac',
    ],

	install_requires = ['Trac'],
	
	entry_points = {
		'trac.plugins': [
			'privatecomments = privatecomments',
		],
	},
)

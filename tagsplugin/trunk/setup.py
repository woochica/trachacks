from setuptools import setup

setup(
    name='TracTags',
    version='0.5',
    packages=['tractags'],
	package_data={'tractags' : ['templates/*.html', 'htdocs/js/*.js', 'htdocs/css/*.css']},
    author='Muness Alrubaie',
    url='http://trac-hacks.org/wiki/TagsPlugin',
    description='Tag plugin for Trac',
    entry_points = {'trac.plugins': ['tractags = tractags']},
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev'],
    install_requires=['Genshi >= 0.5.dev-r698,==dev'],
    )

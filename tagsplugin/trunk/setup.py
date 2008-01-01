from setuptools import setup

setup(
    name='TracTags',
    version='0.6',
    packages=['tractags'],
	package_data={'tractags' : ['templates/*.html', 'htdocs/js/*.js', 'htdocs/css/*.css']},
    author='Muness Alrubaie',
    license='BSD',
    url='http://trac-hacks.org/wiki/TagsPlugin',
    description='Tags plugin for Trac',
    entry_points = {'trac.plugins': ['tractags = tractags']},
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev'],
    install_requires=['Genshi >= 0.5.dev-r698,==dev'],
    )

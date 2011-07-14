from setuptools import setup

setup(name='keywordreplace',
      version='0.0.1',
      packages=['keywordreplace'],
      author='Bangyou Zheng',
      description='Replace keywords with any wiki format from a table in a Wiki page.',
      url='http://trac-hacks.org/wiki/KeywordReplacePlugin',
      license='BSD',
      entry_points = {'trac.plugins': ['keywordreplace = keywordreplace']},
      install_requires = ['Trac >= 0.11'])

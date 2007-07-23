from setuptools import setup

PACKAGE = 'TracPageToODT'
VERSION = '0.2'

setup(name='TracPageToODT',
      version='0.2',
      packages=['pagetoodt'],
      author='Christophe de Vienne',
      author_email='cdevienne@gmail.com',
      description='A plugin for exporting Wiki pages as Open Documents',
      url='http://trac-hacks.org/wiki/PageToOdtPlugin',
      entry_points={'trac.plugins':
     	 ['pagetoodt.pagetoodt=pagetoodt.pagetoodt']})

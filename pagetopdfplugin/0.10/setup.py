from setuptools import setup

PACKAGE = 'TracPageToPDF'
VERSION = '0.2'

setup(name='TracPageToPDF',
      version='0.2',
      packages=['pagetopdf'],
      author='Alec Thomas',
      author_email='alec@swapoff.org',
      description='A plugin for exporting Wiki pages as PDFs',
      url='http://trac-hacks.org/wiki/PageToPdfPlugin',
      entry_points={'trac.plugins': ['pagetopdf.pagetopdf=pagetopdf.pagetopdf']})

from setuptools import setup


setup(name='PageToDoc',
      version='0.2',
      packages=['pagetodoc'],
      author='Lucas Eisenzimmer',
      author_email='lucas.eisenzimmer@t-systems-mms.com',
      maintainer='Mark Mc Mahon',
      maintainer_email='mark.m.mcmahon@gmail.com',
      description='A plugin for exporting Wiki pages as filtered HTML for import into MS Word',
      entry_points={'trac.plugins': ['pagetodoc.pagetodoc=pagetodoc.pagetodoc']})




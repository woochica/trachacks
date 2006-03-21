from setuptools import setup

setup(name='TracHacks',
      version='0.1',
      packages=['trachacks'],
      entry_points={'trac.plugins': 'TracHacks = trachacks'},
      #install_requires=['TracXMLRPC', 'TracAccountManager'],
      )

from setuptools import setup

setup(name='TracPoll',
      version='0.1',
      packages=['tracpoll'],
      entry_points = {'trac.plugins': ['tracpoll = tracpoll']},
      package_data={'tracpoll' : ['htdocs/css/*.css']})

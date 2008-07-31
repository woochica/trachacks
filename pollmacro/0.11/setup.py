from setuptools import setup

setup(name='TracPoll',
      version='0.2',
      packages=['tracpoll'],
      entry_points = {'trac.plugins': ['tracpoll = tracpoll']},
      author='Alec Thomas',
      url='http://trac-hacks.org/wiki/PollMacro',
      license='BSD',
      package_data={'tracpoll' : ['htdocs/css/*.css']})

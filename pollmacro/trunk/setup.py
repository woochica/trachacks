from setuptools import setup

setup(name='TracPoll',
      version='0.3.0',
      packages=['tracpoll'],
      entry_points = {'trac.plugins': ['tracpoll = tracpoll']},
      author='Alec Thomas',
      maintainer = 'Ryan J Ollos',
      maintainer_email = 'ryano@physiosonics.com',
      url='http://trac-hacks.org/wiki/PollMacro',
      license='BSD',
      package_data={'tracpoll' : ['htdocs/css/*.css']})

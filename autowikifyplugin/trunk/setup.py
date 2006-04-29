from setuptools import setup

setup(name='TracAutoWikify',
      version='0.1',
      packages=['tracautowikify'],
      author='Alec Thomas',
      description='Automatically create links for all known Wiki pages, even those that are not in CamelCase.',
      url='http://trac-hacks.org/wiki/AutoWikifyPlugin',
      license='BSD',
      entry_points = {'trac.plugins': ['tracautowikify = tracautowikify']})

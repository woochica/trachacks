from setuptools import setup

setup(name='TracAcronyms',
      version='0.1',
      packages=['tracacronyms'],
      author='Alec Thomas',
      description='Auto-generated acronyms from a table in a Wiki page.',
      url='http://trac-hacks.org/wiki/TracAcronymsPlugin',
      license='BSD',
      entry_points = {'trac.plugins': ['tracacronyms = tracacronyms']})

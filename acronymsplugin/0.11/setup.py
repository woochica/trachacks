from setuptools import setup

setup(name='TracAcronyms',
      version='0.2dev',
      packages=['tracacronyms'],
      author='Alec Thomas',
      description='Auto-generated acronyms from a table in a Wiki page.',
      url='http://trac-hacks.org/wiki/AcronymsPlugin',
      license='BSD',
      entry_points = {'trac.plugins': ['tracacronyms = tracacronyms']},
      install_requires = ['Trac >= 0.11'])

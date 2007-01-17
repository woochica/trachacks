from setuptools import setup


themes = ['blue', 'default', 'dokuwiki', 'flower', 'i18n', 'pixel', 'yatil']

data = ['templates/*.cs', 'htdocs/*.png'] + \
        ['htdocs/ui/%s/*.*' % theme for theme in themes]

setup(name='S5',
      version='0.1',
      packages=['s5'],
      author='Alec Thomas',
      url='http://trac-hacks.org/wiki/S5Plugin',
      license='Public Domain',
      entry_points = {'trac.plugins': ['s5 = s5']},
      package_data={'s5' : data})

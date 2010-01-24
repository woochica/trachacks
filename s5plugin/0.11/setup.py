from setuptools import setup


themes = ['blue', 'default', 'dokuwiki', 'flower', 'i18n', 'pixel', 'yatil']

data = ['templates/*.cs', 'templates/*.html', 'htdocs/*.png'] + \
        ['htdocs/ui/%s/*.*' % theme for theme in themes]

setup(name='S5',
      version='0.2',
      packages=['s5'],
      author='Alec Thomas',
      url='http://trac-hacks.org/wiki/S5Plugin',
      license='Public Domain',
      zip_safe = False,
      entry_points = {'trac.plugins': ['s5 = s5']},
      package_data={'s5' : data})

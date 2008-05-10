from setuptools import setup

setup(name='TracSitemap',
      version='1.0',
      author='Edward S. Marshall',
      author_email='esm@logic.net',
      description='A plugin for Trac which provides Sitemap data.',
      license='BSD',
      keywords='trac sitemap',
      url='http://trac-hacks.org/wiki/TracSitemapPlugin',

      packages=['sitemap'],
      entry_points={'trac.plugins': 'sitemap = sitemap.sitemap'},
)

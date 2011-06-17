from setuptools import setup

PACKAGE = 'TracZotero'
VERSION = '0.0.1'
setup(name=PACKAGE,
      version=VERSION,
      packages=['traczotero'],
      package_data={'traczotero' : ['templates/*.html',
        'htdocs/jquery.treeview/images/*.gif',
        'htdocs/jquery.treeview/lib/*.js',
        'htdocs/jquery.treeview/*.js',
        'htdocs/jquery.treeview/*.css',
        'htdocs/js/*.js',
        'htdocs/images/*.gif',
        'htdocs/css/*.css']},
      author='Bangyou Zheng',
      maintainer='Bangyou Zheng',
      description='Show and cite a local Zotero database',
      url="http://trac-hacks.org/wiki/TracSuposePlugin",
      license='AGPL',
      entry_points = {'trac.plugins': '%s = traczotero' % PACKAGE})

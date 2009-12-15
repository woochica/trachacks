from setuptools import setup

PACKAGE = 'autointertracplugin'

setup(name=PACKAGE,
      version='0.0.1',
      packages=[PACKAGE],
      url='http://www.trac-hacks.org/wiki/AutoInterTracPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
        Automatically make InterTrac links to directories full of trac instances
      """,
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)


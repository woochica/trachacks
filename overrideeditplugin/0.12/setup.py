from setuptools import setup

PACKAGE = 'overrideeditplugin'

setup(name="OverrideEditPlugin",
      version='0.0.6',
      packages=[PACKAGE],
      url='http://www.trac-hacks.org/wiki/OverrideEditPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      Allows you to bypass the warning about the ticket changing since last you loaded it
      """,
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)


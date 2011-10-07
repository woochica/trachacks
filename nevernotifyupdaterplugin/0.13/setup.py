from setuptools import setup

PACKAGE = 'nevernotifyupdaterplugin'

setup(name=PACKAGE,
      version='0.1.2',
      packages=[PACKAGE],
      url='http://www.trac-hacks.org/wiki/NeverNotifyUpdaterPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      Never send emails to the person who made the change. 
      Presumably they already know they made that change.
      """,
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)


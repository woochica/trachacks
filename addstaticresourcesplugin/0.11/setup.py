from setuptools import setup

PACKAGE = 'addstaticresourcesplugin'

setup(name="Add Static Resources Plugin",
      version='0.0.3',
      packages=[PACKAGE],
      url='http://www.trac-hacks.org/wiki/AddStaticResourcesPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
Allows you to add static resource files (css / js) to a page whose url matches a given regex
      """,
      package_data={PACKAGE : ['templates/*.html', 'htdocs/*']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)


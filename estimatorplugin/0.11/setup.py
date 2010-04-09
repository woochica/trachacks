from setuptools import setup

PACKAGE = 'estimatorplugin'

setup(name=PACKAGE,
      version='0.2.0',
      packages=[PACKAGE],
      url='http://www.trac-hacks.org/wiki/EstimatorPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      Produce Detailed Range Based Estimations
      """,
      package_data={PACKAGE : ['templates/*.html', 'htdocs/*']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)


from setuptools import setup

setup(name='estimatorplugin',
      version='1.1',
      packages=['estimatorplugin'],
      url='http://www.trac-hacks.org/wiki/EstimatorPlugin',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Russ Tyndall at Acceleration.net',
      author_email='russ@acceleration.net',
      long_description="""
      Produce Detailed Range Based Estimations
      """,
      package_data={'estimatorplugin' : ['templates/*.html', 'htdocs/*']},
      entry_points={'trac.plugins': ['api=estimatorplugin.api',
                                     'macro=estimatorplugin.macro_provider',
                                     'webui=estimatorplugin.webui']},
)


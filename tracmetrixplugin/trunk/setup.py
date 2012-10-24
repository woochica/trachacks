from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TracMetrixPlugin',
    version='0.1.8',
    keywords='trac plugin metrics statistics',
    url='',
    license='http://www.opensource.org/licenses/bsd-license.php',
    author='Bhuricha Sethanandha at Portland State University',
    author_email='khundeen@gmail.com',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description='Plugin to provide Trac project metrics and statistics',
    long_description="""
    This Trac plugin provides support for project metrics and statistics.

    See http://trac-hacks.org/wiki/TracMetrixPlugin for details.
    """,
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        tracmetrixplugin.mdashboard = tracmetrixplugin.mdashboard
        tracmetrixplugin.web_ui = tracmetrixplugin.web_ui
        tracmetrixplugin.api = tracmetrixplugin.api
        tracmetrixplugin.model = tracmetrixplugin.model
    """,
    package_data={'tracmetrixplugin': ['templates/*.html', 
                                       'htdocs/css/*.css', 
                                       'htdocs/images/*']},
    install_requires = ['Trac >= 0.11.6',
                        'MatPlotLib >= 0.87.7',
                        'NumPy >= 1.0.1'],
)

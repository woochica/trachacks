from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    description='Plugin to provide Trac project metrics and statistics',
    keywords='trac plugin metrics statistics',
    version='0.1.8',
    url='',
    license='http://www.opensource.org/licenses/bsd-license.php',
    author='Bhuricha Sethanandha at Portland State University',
    author_email='khundeen@gmail.com',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryano@physiosonics.com',
    long_description="""
    This Trac 0.11 plugin provides support for project metrics and statistics.

    See http://trac-hacks.org/wiki/TracMetrixPlugin for details.
    """,
    name='TracMetrixPlugin',
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
    install_requires = ['Python >= 2.4', 
                        'Trac >= 0.11.6',
                        'NumPy >= 1.0.1'],
)

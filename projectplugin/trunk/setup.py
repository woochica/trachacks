from setuptools import find_packages, setup

setup(
    name='ProjectPlugin', 
    version='0.4.1',
    author = 'Franz Mayer, Gefasoft AG',
    author_email = 'franz.mayer@gefasoft.de',
    description = 'Adds project information to each ticket.',
    url = 'http://www.gefasoft-muenchen.de',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        projectplugin = projectplugin
    """,
    package_data={'projectplugin': ['htdocs/*.css',
                                    'templates/*.*']}
)
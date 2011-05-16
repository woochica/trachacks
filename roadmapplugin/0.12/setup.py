from setuptools import find_packages, setup

# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Roadmap Plugin', 
    version='0.4.0',
    author = 'Franz Mayer, Gefasoft AG',
    author_email = 'franz.mayer@gefasoft.de', 
    description = 'Sorts roadmap in descending order and adds an filter fields.',
    url = 'http://www.gefasoft-muenchen.de',
    download_url = 'TBD',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        roadmapplugin = roadmapplugin
    """,
    package_data={'roadmapplugin': ['locale/*.*',
                                    'locale/*/LC_MESSAGES/*.*']},
)


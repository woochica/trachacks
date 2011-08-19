from setuptools import find_packages, setup

setup(
    name='TicketDisplay', 
    version='0.4.1',
    author = 'Franz Mayer, Gefasoft AG',
    author_email = 'franz.mayer@gefasoft.de',
    description = 'Some small changes in ticket-view, like having a navigation frame, sorting milestone and version, etc.',
    url = 'http://www.gefasoft-muenchen.de',
    download_url = 'http://trac-hacks.org/wiki/TicketNavPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        ticketnav = ticketnav
    """,
    package_data={'ticketnav': ['templates/*.*', 'htdocs/css/*.css',
                                    'htdocs/js/*.js',
                                    'locale/*.*',
                                    'locale/*/LC_MESSAGES/*.*']}
)
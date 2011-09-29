from setuptools import find_packages, setup

# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Budgeting Plugin', 
    version='0.5.0',
    author = 'Gefasoft AG, Franz Mayer',
    author_email = 'franz.mayer@gefasoft.de', 
    description = 'Adds Budgeting Informations to Tickets',
    url = 'http://www.gefasoft-muenchen.de',
    download_url = 'https://trac-hacks.org/wiki/BudgetingPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        ticketbudgeting = ticketbudgeting
    """,
    package_data={'ticketbudgeting': ['htdocs/js/*.js',
                                      'locale/*.*',
                                      'locale/*/LC_MESSAGES/*.*']},
)


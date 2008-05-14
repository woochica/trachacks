from setuptools import find_packages, setup

setup(
    name = 'TracRelaTicketAdmin',
    version = '0.1',
    packages = ['rtadmin'],
    package_data = { 'rtadmin': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "RelaTicket Admin plugin for Trac.",
    license = "BSD",
    keywords = "trac rela ticket admin",
    url = "http://trac-hacks.org/wiki/RelaTicketAdmin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],
    entry_points = {'trac.plugins': ['rtadmin = rtadmin.relaticketadmin']},
)

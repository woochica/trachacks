from setuptools import find_packages, setup

setup(
    name = 'TracTicketTemplate',
    version = '0.6',
    packages = ['tickettemplate'],
    package_data = { 'tickettemplate': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Ticket template plugin for Trac.",
    license = "LGPLv2.1",
    keywords = "trac ticket template",
    url = "http://trac-hacks.org/wiki/TracTicketTemplatePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],
    entry_points = {'trac.plugins': ['tickettemplate = tickettemplate.ttadmin']},
)

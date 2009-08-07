from setuptools import find_packages, setup

setup(
    name = 'TracTicketValidator',
    version = '0.1',
    packages = ['ticketvalidator'],
    package_data = { 'ticketvalidator': [ '*.txt' ] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Ticket validator plugin for Trac.",
    license = "LGPLv2.1",
    keywords = "trac ticket validator",
    url = "http://trac-hacks.org/wiki/TracTicketValidatorPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = [],
    entry_points = {'trac.plugins': ['ticketvalidator = ticketvalidator.ticketvalidator']},
)

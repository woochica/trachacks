from setuptools import find_packages, setup
#, 'htdocs/*.*'
setup(
    name = 'AgiloTicketReport',
    version = '0.1',
    packages = ['AgiloTicketReport'],
    package_data = { 'AgiloTicketReport': ['templates/*.*'] },

    author = "Tod Jiang",
    author_email = 'tod@cherrymind.com',
    maintainer = 'Tod',
    maintainer_email = "tod@cherrymind.com",
    description = "Ticket Working Hours Report plugin for Trac with Aglio plugin.",
    license = "BSD",
    keywords = "trac agilo ticket report",
    url = "",
	
    install_requires = ['trac >= 0.11',
						],
    entry_points = {'trac.plugins': ['AgiloTicketReport = AgiloTicketReport.ticketreport']},
)

from setuptools import setup

setup(
    name = 'DuplicateTicketSearch', 
    version = '1.0.1',
    author = 'gregmac',
	license = 'BSD',
    description = 'Adds XMLRPC-based check from ticket entry page for potential duplicate tickets.',
    keywords = 'trac duplicate ticket search plugin',
    url = 'http://trac-hacks.org/wiki/DuplicateTicketSearchPlugin',
    packages = ['duplicateticketsearch'],
    package_data = { 'duplicateticketsearch' : ['htdocs/css/*.css', 'htdocs/js/*'] },
    entry_points = """
        [trac.plugins]
        DuplicateTicketSearch = duplicateticketsearch
    """,
    install_requires = ['TracXMLRPC'],  
)
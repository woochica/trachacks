from setuptools import setup

setup(
    name='DuplicateTicketSearch', 
    version='1.0',
    packages=['duplicateticketsearch'],
    package_data = { 'duplicateticketsearch' : ['htdocs/css/*.css', 'htdocs/js/*'] },
    entry_points = """
        [trac.plugins]
        DuplicateTicketSearch = duplicateticketsearch
    """,
    author = 'gregmac', 
    description = 'Adds XMLRPC-based check from ticket entry page for potential duplicates', 
)

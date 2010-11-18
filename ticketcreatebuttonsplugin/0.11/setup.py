from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TicketCreateButtons', version='0.1',
    author="Chris Nelson",
    packages=find_packages(exclude=['*.tests*']),
    url="http://trac-hacks.org/wiki/TicketCreateButtonsPlugin",
    entry_points = """
        [trac.plugins]
        ticketCreateButtons=ticketCreateButtons
    """,
)


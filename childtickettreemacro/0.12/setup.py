from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name = 'Tracchildtickettreemacro',
    version = '1.0.0',
    packages = find_packages(),
    author = 'Mark Ryan',
    author_email = 'walnut.trac.hacks@gmail.com',
    description = 'Macro to see a complete tree/hierarchy of tickets under the given ticket number.',
    keywords = 'trac plugins ticket dependency childtickets',
    url = 'http://trac-hacks.org/wiki/ChildTicketTreeMacro',
    install_requires = ['Trac>=0.12', 'Genshi>=0.5', 'Python>=2.4'],
    entry_points = { 'trac.plugins' : 'childtickettree = childtickettree' },
)

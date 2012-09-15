'''
Created on Aug 5, 2009

@author: Bart Ogryczak
'''
from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='BacklogPlugin', 
    version='0.1.34',
    packages=['backlog'],
    author='Bart Ogryczak',
    author_email='bartlomiej.ogryczak@hyves.nl',
    url='http://trac-hacks.org/wiki/BacklogPlugin',   
    license='BSD',
    description="""Allows multiple backlogs """,
    zip_safe = True,
    entry_points = {
        'trac.plugins':
        ['backlog.db = backlog.db',
         'backlog.ticketchangelistener = backlog.ticketchangelistener',
         'backlog.web_ui = backlog.web_ui',                
         ],
        },
    package_data={'backlog': ['templates/*.html',
                              'htdocs/css/*.css',
                              'htdocs/js/*.js',
                              'htdocs/images/*']},
)

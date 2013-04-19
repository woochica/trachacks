from setuptools import find_packages, setup

version='0.12'

setup(name='GeoTicket',
      version=version,
      description="add geolocations to Trac tickets",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/GeoTicketPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'geoticket': ['templates/*', 'htdocs/js/*'] },
      zip_safe=False,
      install_requires=[
        # -*- Extra requirements: -*-
        'geopy>=0.93dev',
        'CustomFieldProvider',
        'TicketSidebarProvider',
        'TracSQLHelper',
        'ComponentDependencyPlugin',
        'simplejson',
        ],
      extras_require={
        'mail2trac': [ 'mail2trac' ],
        },
      dependency_links=[
        "http://geopy.googlecode.com/svn/branches/reverse-geocode#egg=geopy-0.93dev",
        "http://trac-hacks.org/svn/customfieldproviderplugin/0.11#egg=CustomFieldProvider",
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
        "http://trac-hacks.org/svn/mailtotracplugin/0.11/#egg=mail2trac",
        "http://trac-hacks.org/svn/tracsqlhelperscript/0.11#egg=TracSQLHelper",
        "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
        ],
      entry_points = """
      [trac.plugins]
      geoticket = geoticket.ticket
      mapsidebar = geoticket.web_ui
      mapmarkers = geoticket.marker
      geoquery = geoticket.query 
      georegions = geoticket.regions
      geoticketmail = geoticket.mail [mail2trac]
      """,
      )


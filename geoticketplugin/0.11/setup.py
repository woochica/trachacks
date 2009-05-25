from setuptools import find_packages, setup

version='0.5'

setup(name='GeoTicket',
      version=version,
      description="add geolocations to Trac tickets",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://oss.openplans.org/MobileGeoTrac',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'geoticket': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      install_requires=[
        # -*- Extra requirements: -*-
        'geopy',
        'CustomFieldProvider',
        'TicketSidebarProvider',
        'simplejson'
        ],
      extras_require={
        'mail2trac': [ 'mail2trac' ],
        },
      dependency_links=[
        "http://trac-hacks.org/svn/customfieldproviderplugin/0.11#egg=CustomFieldProvider",
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
        "http://trac-hacks.org/svn/mailtotracplugin/0.11/#egg=mail2trac",
        ],
      entry_points = """
      [trac.plugins]
      geoticket = geoticket.ticket
      mapsidebar = geoticket.web_ui
      geoticketmail = geoticket.mail [mail2trac]
      """,
      )


from setuptools import find_packages, setup

version='0.0'

setup(name='GeoTrac',
      version=version,
      description="add geolocations to Trac tickets",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://oss.openplans.org/MobileGeoTrac',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'geotrac': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      install_requires=[
        # -*- Extra requirements: -*-
        'geopy',
        'CustomFieldProvider',
        'TicketSidebarProvider'
        ],
      dependency_links=[
        "http://trac-hacks.org/svn/customfieldproviderplugin/0.11#egg=CustomFieldProvider",
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
        ],
      entry_points = """
      [trac.plugins]
      geotrac = geotrac.ticket
      mapsidebar = geotrac.web_ui
      """,
      )


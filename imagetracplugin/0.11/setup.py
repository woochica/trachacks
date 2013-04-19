from setuptools import find_packages, setup

version='0.4'

setup(name='ImageTrac',
      version=version,
      description="attach an image to a Trac ticket upon ticket creation",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/ImageTracPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'imagetrac': ['templates/*', 'htdocs/css/*', 'htdocs/js/*'] },
      zip_safe=False,
      install_requires=[
        'ComponentDependencyPlugin',
        'TicketSidebarProvider',
        'PIL',
        'cropresize',
        'TracSQLHelper',
        ],
      extras_require={ 'geo': [ 'GeoTicket' ] },
      dependency_links=[
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
        "http://trac-hacks.org/svn/tracsqlhelperscript/0.11#egg=TracSQLHelper",
        "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
        "http://dist.repoze.org/PIL-1.1.6.tar.gz",
        ],
      entry_points = """
      [trac.plugins]
      imagetrac = imagetrac.image
      imagesidebar = imagetrac.web_ui
      defaultimage = imagetrac.default_image
      mapimagemarker = imagetrac.geo [geo]
      """,
      )

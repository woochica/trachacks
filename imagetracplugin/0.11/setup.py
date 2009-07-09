from setuptools import find_packages, setup

version='0.2'

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
      package_data={ 'imagetrac': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      install_requires=[
        'TicketSidebarProvider',
        'PIL'
        ],
      extras_require={
        'mail2trac': [ 'mailtrac' ],
        },
      dependency_links=[
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
        "http://trac-hacks.org/svn/mailtotracplugin/0.11/#egg=mail2trac",
        "http://dist.repoze.org/PIL-1.1.6.tar.gz",
        ],
      entry_points = """
      [trac.plugins]
      imagetrac = imagetrac.image
      imagesidebar = imagetrac.web_ui
      imagetracmail = imagetrac.mail [mail2trac]
      """,
      )

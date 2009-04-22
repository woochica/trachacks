from setuptools import find_packages, setup

version='0.0'

setup(name='ImageTrac',
      version=version,
      description="attach an image to a Trac ticket upon ticket creation",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'imagetrac': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      install_requires=[
        # -*- Extra requirements: -*-
        'TicketSidebarProvider',
        ],
      extras_require={
        'mail2trac': [ 'mailtrac' ],
        },
      dependency_links=[
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
        "http://trac-hacks.org/svn/mailtotracplugin/0.11/#egg=mail2trac",
        ],
      entry_points = """
      [trac.plugins]
      imagetrac = imagetrac.image
      imagesidebar = imagetrac.web_ui
      imagetracmail = imagetrac.mail [mail2trac]
      """,
      )

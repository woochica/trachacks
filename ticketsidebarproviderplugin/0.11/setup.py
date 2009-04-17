from setuptools import find_packages, setup

version='0.0'

setup(name='TicketSidebarProvider',
      version=version,
      description="add content to the ticket sidebar",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'ticketsidebarprovider': ['templates/*', 'htdocs/**'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      ticketsidebarprovider = ticketsidebarprovider
      """,
      )


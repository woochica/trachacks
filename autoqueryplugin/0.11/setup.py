from setuptools import find_packages, setup

version='0.1.2'

setup(name='AutoQuery',
      version=version,
      description="in ticket summary, each of the ticket attributes (milestone, priority, owner, etc) to contain a generated link to a custom query consisting of all tickets with that attribute value.",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='https://svn.openplans.org/svn/TracPlugins/',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      autoquery = autoquery
      """,
      )


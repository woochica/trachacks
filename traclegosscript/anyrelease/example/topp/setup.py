from setuptools import find_packages, setup

version='0.0'

setup(name='TOPPTracProject',
      version=version,
      description="The Open Planning Project Trac Template",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://topp.openplans.org',
      keywords='trac project',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      install_requires = [ 'PasteScript', 'TracLegos' ],
      dependency_links = [
      "https://svn.openplans.org/svn/trac/install/TracLegos#egg=TracLegos",
      ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      topp_trac_project = topptracproject.project:ToppTracProject
      """,
      )


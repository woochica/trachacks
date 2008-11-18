from setuptools import find_packages, setup

version='0.1'

setup(name='OSSTracProject',
      version=version,
      description="Open Source Software Project Trac Template",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac project OSS',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      install_requires = [ 'PasteScript', 'TracLegos' ],
      dependency_links = [
      "http://trac-hacks.org/svn/traclegosscript/anyrelease#egg=TracLegos",
      ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      oss_project = osstracproject.project:OSSTracProject
      """,
      )


from setuptools import find_packages, setup

version='0.11r1'

setup(name='sensitivetickets',
      version=version,
      description="A trac plugin that lets you mark tickets as 'sensitive' with a check box.  Those tickets can only be seen with permission.  This plugin is based on the example plugin http://trac.edgewall.org/browser/trunk/sample-plugins/permissions/vulnerability_tickets.py",
      author='Jeff Hammel and Sebastian Benthall',
      author_email='jhammel@openplans.org',
      maintainer = 'Daniel Kahn Gillmor',
      maintainer_email = 'dkg@fifthhorseman.net',
      url='http://trac-hacks.org/wiki/SensitiveTicketsPlugin',
      keywords='trac plugin security',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      sensitivetickets = sensitivetickets
      """,
      )


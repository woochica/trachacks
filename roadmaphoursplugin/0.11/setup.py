from setuptools import find_packages, setup

version='0.5'

setup(name='RoadmapHours',
      version=version,
      description="Display estimated and actual hours in roadmap",
      long_description="""
Provides an implementation of ITicketGroupStatsProvider that uses
the actual and estimated hour fields from the Timing and Estimation
plugin to draw the roadmap stats.

You will need to set the status_provider under [roadmap] in trac.ini
to RoadmapHoursTicketGroupStatsProvider.
""",
      author='Joshua Hoke',
      author_email='',
      url='',
      keywords='trac plugin',
      license="GPL",
      packages=['roadmaphours'],
      install_requires=['timingandestimationplugin'],
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      roadmaphours = roadmaphours
      """
      )


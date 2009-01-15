from setuptools import setup

PLUGIN_NAME = 'MilestoneTeams'
PACKAGE_NAME = 'milestoneteams'

setup(
    name = PLUGIN_NAME,
    description = 'Plugin to support developer teams for milestones',
    keywords = 'trac plugin milestone team',
    version = '0.1',
    url = 'http://trac-hacks.org/wiki/MilestoneTeamsPlugin',
    license = 'http://www.opensource.org/licenses/mit-license.php',
    author = 'Matthew Chretien',
    author_email = 'silvein+milestoneteams@gmail.com',
    long_description = """
    This Trac 0.11 plugin adds support for per-milestone developer teams.

    When a ticket is assigned to a milestone, the team assigned to that milestone will be notified.
    """,
    packages = [ PACKAGE_NAME ],
    package_data = { PACKAGE_NAME : [ 'templates/*.html', 'htdocs/*' ] },
    entry_points = { 'trac.plugins' : '%s = %s' % (PACKAGE_NAME, PACKAGE_NAME) },
)

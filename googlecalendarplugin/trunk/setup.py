from setuptools import setup

PACKAGE = 'GoogleCalendar'
VERSION = '0.1.2'
DESCRIPTION = 'Provides an integration of a Google Calendar IFRAME into Trac'
AUTHOR = 'Stefan Simroth'
AUTHOR_EMAIL = 'stefan.simroth@gmail.com'
PROJECT_HOME = 'http://trac-hacks.org/wiki/GoogleCalendarPlugin'
LICENSE = 'BSD'

setup(name=PACKAGE,
      version=VERSION,
      description = DESCRIPTION,
      author = AUTHOR,
      author_email = AUTHOR_EMAIL,
      url = PROJECT_HOME,
      license = LICENSE,
      long_description =
"""\
Provides an integration of a Google Calendar IFRAME into Trac
""",
      packages=['googlecalendar'],
      entry_points={'trac.plugins': '%s = googlecalendar' % PACKAGE},
      package_data={'googlecalendar': ['templates/*.cs']},
)


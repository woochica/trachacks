from setuptools import setup
import pkg_resources

pkg_resources.require("TracUserManagerPlugin>=0.4")

PACKAGE = 'TicketTeamDispatcher'
PACKAGE_SHORT = 'ttd'
VERSION = '0.2'

setup(
    name=PACKAGE,
    version=VERSION,
    packages=[PACKAGE_SHORT],
    package_data={PACKAGE_SHORT: ['tpl/*']},
    author_email = 'Alexander von Bremen-Kuehne',
    url = 'http://trac-hacks.org/wiki/TicketTeamDispatcherPlugin',
    license = 'GPLv2 or later',
    description = 'Sends mails on ticket-creation to specified addresses according to the selected team.',                      
    entry_points = """
        [trac.plugins]
        %(pkg)s = %(pkg_s)s
    """ % {'pkg': PACKAGE, 'pkg_s' : PACKAGE_SHORT },
)


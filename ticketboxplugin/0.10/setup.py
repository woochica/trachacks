from setuptools import setup

PACKAGE = 'TracTicketBox'
VERSION = '0.1'

setup(name='TracTicketBox',
      version='0.1',
      packages=['ticketbox'],
      author='jacques witte & Shun-ichi Goto',
      author_email='jacques.witte@usineweb.fr',
      description='A plugin for TicketBox + additional features (ticket_report, table_report)',
      url='http://trac-hacks.org/wiki/TicketBoxPlugin',
      entry_points={'trac.plugins': ['ticketbox.ticketbox=ticketbox.ticketbox']})

from setuptools import find_packages, setup

setup(name='TicketConditionalCreationStatusPlugin',
      version='0.2',
      packages=find_packages(exclude=''),
      package_data={},
      author='Patrick Schaaf',
      author_email='trachacks@bof.de',
      description='Set ticket creation status conditioned on ticket type or other fields',
      url='https://trac-hacks.org/wiki/TicketConditionalCreationStatusPlugin',
      license='GPLv2',
      entry_points={'trac.plugins': ['ticketconditionalcreationstatus = ticketconditionalcreationstatus']},
)

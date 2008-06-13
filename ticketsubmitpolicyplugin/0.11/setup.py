from setuptools import find_packages, setup

version='0.6'

setup(name='TicketSubmitPolicy',
      version=version,
      description="trac plugin to dictate ticket form submission policy for new and existing tickets",
      long_description="""
Trac has a workflow policy for tickets to go from one state to another.  
It doesn't (to the best of my knowledge?) have any way of setting up custom 
types of tickets:  tickets to which various form fields are either mandatory
or not-applicable.  This plugin provides a javascript guard against form
submission and enforcement of a ticket submission where ticket fields 
function according to the value of other ticket fields.
""",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/TicketSubmitPolicyPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      ticketsubmitpolicy = ticketsubmitpolicy
      """,
      )


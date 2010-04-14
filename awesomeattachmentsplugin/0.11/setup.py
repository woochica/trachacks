from setuptools import setup

setup(
    name='awesomeAttachmentsPlugin', version='0.1',
    packages=['ticket'],
    package_data={ 'ticket': [ 'htdocs/images/*' ]},
    entry_points = """
        [trac.plugins]
        ticketupload = ticket.ticketupload
    """,
)

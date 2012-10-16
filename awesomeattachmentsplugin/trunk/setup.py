from setuptools import setup

setup(
    name='AwesomeAttachmentsPlugin', version='0.2',
    packages=['awesome'],
    package_data={ 'awesome': [ 'htdocs/images/*', 'htdocs/js/*', 'htdocs/css/*' ]},
    entry_points = """
        [trac.plugins]
        awesome = awesome.awesomeattachments
    """,
)

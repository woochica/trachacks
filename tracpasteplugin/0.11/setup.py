from setuptools import setup

PACKAGE = 'tracpaste'
VERSION = '0.2'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Add a pastebin to the trac',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    url='http://trac.pocoo.org/',
    license='BSD',
    packages=['tracpaste'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    package_data={
        'tracpaste' : ['templates/*.html', 'htdocs/*.css']
    },
    entry_points = {
        'trac.plugins': ['tracpaste = tracpaste']
    }
)

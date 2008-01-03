from setuptools import setup

setup(
    name='IRC Announcer',
    version='0.1',
    description='Announce trac changes to an IRC bot',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    url='http://trac-hacks.org/wiki/IrcAnnouncerPlugin',
    license='BSD',
    packages=['tracext', 'tracext.ircannouncer'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    entry_points={
        'trac.plugins': 'ircannouncer = tracext.ircannouncer'
    }
)

from setuptools import setup

PACKAGE = 'TracHgrcEdit'
VERSION = '0.11.0'

setup(
    name = PACKAGE,
    version = VERSION,
    author = "Matthias Bilger",
    author_email = "matthias@bilger.info",
    description = "A interface to edit hgrc file via admin panel",
    license = "BSD",
    keywords = "trac plugin mercurial hgrc",
    packages=['hgrcedit'],
    entry_points={'trac.plugins': '%s = hgrcedit' % PACKAGE},
    package_data={'hgrcedit': ['templates/*.html']},
)

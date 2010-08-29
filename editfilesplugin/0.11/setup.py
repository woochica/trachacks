from setuptools import setup

PACKAGE = 'EditFilePlugin'
VERSION = '0.11.1.1'

setup(
    name = PACKAGE,
    version = VERSION,
    author = "",
    author_email = "",
    maintainer = "",
    maintainer_email = "",
    description = "A interface to edit files in admin panel",
    license = "BSD",
    keywords = "trac plugin files",
    url = "http://trac-hacks.org/wiki/EditFilePlugin",
    packages=['edit_file'],
    entry_points={'trac.plugins': '%s = edit_file' % PACKAGE},
    package_data={'edit_file': ['templates/*.html']},
)

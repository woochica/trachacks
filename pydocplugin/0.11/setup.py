from setuptools import setup

PACKAGE = 'TracPyDoc'
VERSION = '0.11.1'

setup(
    name=PACKAGE,
    version=VERSION,
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    maintainer = "Christian Boos",
    maintainer_email = "cboos@neuf.fr",
    description = "Browse Python documentation from within Trac.",
    long_description = """
    Browse Python documentation as prepared by the pydoc system
    from within Trac.""",
    license = "BSD",
    keywords = "trac plugin python documentation pydoc",
    url='http://trac-hacks.swapoff.org/wiki/PyDocPlugin',
    packages=['tracpydoc'],
    package_data={'tracpydoc' : ['templates/*.html', 'htdocs/css/*.css']},

    entry_points = {
        'trac.plugins': [
            'tracpydoc.tracpydoc = tracpydoc.tracpydoc'
        ]
    },
    )

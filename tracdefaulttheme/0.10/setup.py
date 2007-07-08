from setuptools import setup

PACKAGE = 'TracDefaultTheme'
VERSION = '0.1'

setup(
    name = PACKAGE,
    version = VERSION,
    author = "Robert Barsch",
    author_email = "barsch@lmu.de",
    description = "Trac default theme",
    license = "BSD",
    keywords = "trac theme",
    url = "http://www.geophysik.lmu.de/~barsch/projects/TracDefaultTheme",
    classifiers = [ 'Framework :: Trac', ],
    install_requires = ['TracThemeEngine'],
    packages=['defaulttheme'],
    entry_points={'trac.plugins': 'defaulttheme.theme = defaulttheme.theme'},
    package_data={'defaulttheme': ['htdocs/*.*' ] },
)

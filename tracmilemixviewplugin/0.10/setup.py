from setuptools import find_packages, setup

setup(
    name = 'TracMileMixViewAdmin',
    version = '0.2',
    packages = ['mmv'],
    package_data = { 'mmv': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "MMV plugin for Trac.",
    license = "BSD",
    keywords = "trac MMV",
    url = "http://trac-hacks.org/wiki/MMV",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],
    entry_points = {'trac.plugins': ['mmv = mmv.web_ui']},
)

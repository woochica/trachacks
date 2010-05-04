from setuptools import find_packages, setup

setup(
    name = 'TracAutoComplete',
    version = '0.1',
    packages = ['autocomplete'],
    package_data = {
        'autocomplete': ['*.txt', 
                 'htdocs/*.*',
                 'htdocs/images/*.*',
                 'htdocs/jquery-ui/*.*',
                 'htdocs/jquery-ui/images/*.*',
                 'templates/*.*',
                ]
    },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Auto complete plugin for Trac.",
    license = "BSD",
    keywords = "trac svg",
    url = "http://trac-hacks.org/wiki/TracAutoCompletePlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {'trac.plugins': ['autocomplete = autocomplete.web_ui']},
)

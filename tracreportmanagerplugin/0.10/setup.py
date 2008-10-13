from setuptools import find_packages, setup

setup(
    name = 'TracReportManager',
    version = '0.1',
    packages = ['reportmanager'],
    package_data = { 'reportmanager': [ '*.txt', 'templates/*.*', 'htdocs/*.*'] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Report manager plugin for Trac.",
    license = "BSD",
    keywords = "trac report manager",
    url = "http://trac-hacks.org/wiki/TracReportManagerPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],
    entry_points = {'trac.plugins': ['reportmanager = reportmanager.reportmanager']},
)

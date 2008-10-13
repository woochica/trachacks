from setuptools import find_packages, setup

setup(
    name = 'TracScheduler',
    version = '0.1',
    packages = ['tracscheduler'],
    package_data = { 'tracscheduler': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },
    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Trac Scheduler plugin for Trac.",
    license = "BSD",
    keywords = "trac scheduler",
    url = "http://trac-hacks.org/wiki/TracSchedulerPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [],
    entry_points = {'trac.plugins': ['tracscheduler = tracscheduler.web_ui']},
)
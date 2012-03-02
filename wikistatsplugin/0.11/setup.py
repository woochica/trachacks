from setuptools import setup

setup(
    name='TracWikiStats',
    author = 'RottenChester',
    author_email = 'rottenchester@gmail.com',
    maintainer = 'Ryan J Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    url = 'http://trac-hacks.org/wiki/WikiStatsPlugin',
    license = 'bsd',
    version='0.1',
    packages=['wikistats'],
    package_data={ 'wikistats': [  ]},
    description="Macros to display wiki stats",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
                'wikistats.stats = wikistats.stats',
                'wikistats.usercount = wikistats.usercount',
        'wikistats.pagecount = wikistats.pagecount'
                ],
    }
)


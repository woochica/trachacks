from setuptools import setup

setup(
    name='TracIncludePagesMacro',
    version='0.1',
    author = 'RottenChester',
    author_email = 'rottenchester@gmail.com',
    url = 'http://trac-hacks.org/wiki/TracIncludePagesPlugin',
    license = 'bsd',
    packages=['includepages'],
    package_data={ 'includepages': [  ]},
    description="Macro to include other pages in a wiki page",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
                'includepages.macro = includepages.macro',
                ],
    }
)
      

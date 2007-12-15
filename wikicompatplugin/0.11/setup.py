from setuptools import setup

setup(
    name='TracWikiCompat',
    author = 'RottenChester',
    author_email = 'rottenchester@gmail.com',
    url = 'http://trac-hacks.org/wiki/WikiCompatPlugin',
    license = 'bsd',
    version='0.1',
    packages=['wikicompat'],
    package_data={ 'wikicompat': [  ]},
    description="Macros for compatibility with Sycamore and other Moin-like wikis",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
                'wikicompat.mailto = wikicompat.mailto',
                'wikicompat.stop = wikicompat.stop',
		'wikicompat.nbsp = wikicompat.nbsp',
                'wikicompat.note = wikicompat.note',
                'wikicompat.anchor = wikicompat.anchor'
                ],
    }
)
      

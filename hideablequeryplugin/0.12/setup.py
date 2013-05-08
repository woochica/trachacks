from setuptools import setup

setup(
    name='hideable_query',
    version='0.1',
    packages=['hideable_query'],

    author='Michael Henke',
    author_email='michael.henke@she.net',
    description="A trac plugin that lets you hide the query site and the links to it",
    license="GPL",

    keywords='trac plugin security hide query report',
    url='http://trac-hacks.org/wiki/HideableQueryPlugin',

    classifiers=[
        'Framework :: Trac',
    ],

    install_requires=['Trac'],

    entry_points={
        'trac.plugins': [
            'hideable_query = hideable_query',
        ],
    },
)

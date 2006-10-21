#!/usr/bin/env python
from setuptools import setup, find_packages

version = '0.1'

setup(
    name='TracPygments',
    version=version,
    description="Trac syntax colorer using Pygments",
    long_description=""" """,
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License', 
    ],
    keywords='',
    author='Matt Good',
    author_email='matt@matt-good.net',
    url='http://matt-good.net',
    license='BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'Pygments',
    ],
    entry_points={
        'trac.plugins': [
            'tracpygments = tracpygments',
        ],
    }
)

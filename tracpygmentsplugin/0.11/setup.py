#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='TracPygments',
    version='0.2',
    description="Trac syntax colorer using Pygments",
    long_description=""" """,
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License', 
    ],
    keywords='trac.mimeview',
    author='Matt Good',
    author_email='matt@matt-good.net',
    url='http://trac-hacks.org/wiki/TracPygmentsPlugin',
    license='BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'Pygments >= 0.5',
    ],
    entry_points={
        'trac.plugins': [
            'tracpygments = tracpygments',
        ],
    }
)

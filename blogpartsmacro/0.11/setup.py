# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracBlogParts',
    version='0.1',
    author='Kazuya Hirobe',
    author_email='',
    url='',
    description='Macro and web admin page to use blog parts in Trac',
    zip_safe=True,
    packages=['blogparts'],
    package_data={
        'blogparts': ['templates/*.html',]
        },
    entry_points={
        'trac.plugins': 'TracBlogParts = blogparts'
        },
    )

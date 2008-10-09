#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'CiteMacro',
    version = '0.1',
    packages = ['cite'],
    author = 'Louis Cordier',
    author_email = 'lcordier@gmail.com',
    description = "Macro to allow for the citation of resources."
                  "Gives wikipages the equivalent to LaTeX's \cite{} and \makeindex commands.",
    url = '',
    license = 'BSD',
    keywords = 'trac plugin cite macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['cite.macro = cite.macro']}
)

# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
	name='TracDocBook',
	version='0.2.2',
	author = 'William Ghelfi',
	author_email = 'trumbitta@gmail.com',
	url = 'http://trac-hacks.org/wiki/TracDocBookPlugin',
	description = 'DocBook syntax interpreter for Trac Wiki',
	license = 'GPL version 2',
	packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'tracdocbook = tracdocbook',
        ]
    },
)
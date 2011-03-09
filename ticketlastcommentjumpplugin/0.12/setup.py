#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
from trac.util.dist import get_l10n_cmdclass
extra = {}
cmdclass = get_l10n_cmdclass()

if cmdclass:
    extra['cmdclass'] = cmdclass
    extractors = [
        ('**.py', 'python', None),
        ('**/templates/**.html', 'genshi', None),
    ]
    extra['message_extractors'] = {
        'TicketLastCommentJump': extractors,
    }

setup(
    name='TicketLastCommentJumpPlugin', version='0.1',
    author = "wadatka",
    author_email = "wadatka@gmail.com",
    description = "Add link to last comment in the ticket.",
    license = "BSD",
    url = "",
    zip_safe = False,
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        TicketLastCommentJump = TicketLastCommentJump
    """,
    package_data={
        'TicketLastCommentJump': [
                'locale/*/LC_MESSAGES/*.mo',
        ]
    },
    **extra
)


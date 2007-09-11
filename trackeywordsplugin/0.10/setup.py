# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from setuptools import find_packages, setup

setup(
    name='TracKeywordsPlugin',
    version=0.1,
    description="Allows adding and removing keywords on a ticket from a list",
    author="Thomas Vander Stichele",
    author_email="thomas at apestaart dot org",
    license="BSD",
    # url=
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'trackeywords': [
            'templates/*.cs',
            'README', 'TODO', 'ChangeLog'
        ]
    },
    entry_points = """
        [trac.plugins]
        trackeywords = trackeywords.web_ui
    """,
    #test_suite="trackeywords.tests",
)

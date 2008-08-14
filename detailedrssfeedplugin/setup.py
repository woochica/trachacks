# Copyright (C) 2003-2008 Fetch Softworks LLC
# All rights reserved.
#
# This software is licensed as described in the file license.txt, which
# you should have received as part of this distribution.


from setuptools import find_packages, setup

setup(
    name='ReportToDetailedRSS', version='1.0.1',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        ReportToDetailedRSS = ReportToDetailedRSS
    """,
    package_data={'ReportToDetailedRSS': ['templates/*.rss']},
)
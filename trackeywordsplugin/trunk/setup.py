# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Thomas Vander Stichele <thomas at apestaart dot org>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer
#    in this position and unchanged.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from setuptools import find_packages, setup

setup(
    name='TracKeywordsPlugin',
    version=0.3,
    description="Allows adding and removing keywords on a ticket from a list",
    author="Thomas Vander Stichele",
    author_email="thomas at apestaart dot org",
    license="BSD",
    url="trac-hacks.org/wiki/TracKeywordsPlugin",
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'trackeywords': [
            'templates/*.html',
            'README', 'TODO', 'ChangeLog'
        ]
    },
    entry_points = """
        [trac.plugins]
        trackeywords = trackeywords.web_ui
    """,
    #test_suite="trackeywords.tests",
)

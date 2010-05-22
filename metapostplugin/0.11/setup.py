"""
Copyright (c) 2010 Andrey Sergievskiy. All rights reserved.

Python egg setup file for the metapost trac wiki processor.

"""


__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.0.1'

from setuptools import setup, find_packages

setup (
    name = 'metapost',
    version = __version__,
    packages = find_packages(),
    package_data = { 'metapost' : ['examples/*',],
    },
    entry_points={'trac.plugins': 'metapost = metapost'},
    author = "Andrey Sergievskiy",
    author_email = "seas@andreysergievskiy.com",
    keywords = "trac metapost",
    url = "http://trac-hacks.org/wiki/MetaPostPlugin",
    description = "MetaPost plugin for Trac 0.11",
    long_description = """
    The MetaPost wiki processor is a plugin for Trac that allows the
dynamic generation of MetaPost diagrams. The
text of a wiki page can contain the source text for metapost and the
web browser will show the resulting image.""",
    license = """Copyright (C) 2010 Andrey Sergievskiy
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
 3. The name of the author may not be used to endorse or promote
    products derived from this software without specific prior
    written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""",
)

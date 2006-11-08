"""
$Id$
$HeadURL$

Copyright (c) 2006 Harald Radi. All rights reserved.

Python egg setup file for the buildbot trac wiki processor.
"""


__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL'
__docformat__ = 'restructuredtext'



from setuptools import setup


PACKAGE = 'TracGoogleSitemaps'
VERSION = '0.1'


setup(name=PACKAGE,
      version=VERSION,
      packages=['TracGoogleSitemaps'],
      package_data={'TracGoogleSitemaps' : []},
      entry_points={'trac.plugins': '%s = TracGoogleSitemaps' % PACKAGE},
      author = "Harald Radi",
      author_email = "harald.radi@nme.at",
      keywords = "trac google sitemaps",
      url = "http://trac-hacks.org/wiki/GoogleSitemapsPlugin",
      description = "Google Sitemaps plugin for Trac",
      long_description = """The Google Sitemaps plugin for Trac creates a sitemap that can be submitted to google. It also handles the owner confirmation request.""",
      license = """Copyright (c) 2006 Harald Radi
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

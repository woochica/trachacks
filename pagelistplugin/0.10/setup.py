"""
$Id$
$HeadURL$

Copyright (c) 2006 Peter Kropf. All rights reserved.

Python egg setup file for the buildbot trac wiki processor.
"""


__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'



from setuptools import setup


PACKAGE = 'TracPageList'
VERSION = '0.1.0'


setup(name=PACKAGE,
      version=VERSION,
      packages=['TracPageList'],
      package_data={'TracPageList' : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = TracPageList' % PACKAGE},
      author = "Peter Kropf",
      author_email = "pkropf@gmail.com",
      keywords = "trac pagelist",
      url = "http://trac-hacks.swapoff.org/wiki/PageListPlugin",
      description = "PageList plugin for Trac",
      long_description = """The PageList plugin for Trac creates dynamic wiki link pages that
contain wiki names that match a suffix. This allows for the creation
of wiki pages with a common suffix (NameOneHowTo, NameTwoHowTo,
NameThreeHowTo, etc.) to be listed in an index like page via a
PageList wiki command - pagelist:HowTo.""",
    license = """Copyright (C) 2006 Peter Kropf
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

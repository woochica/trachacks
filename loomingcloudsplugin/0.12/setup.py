# Copyright (c) Jeff Hammel
# Copyright (c) 2010, Rowan Wookey www.obsidianproject.co.uk
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright 
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <ORGANIZATION> nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

from setuptools import find_packages, setup

version='0.12r1'

setup(name='LoomingClouds',
      version=version,
      description="inline clouds for ticket.html",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      maintainer = 'Rowan Wookey',
      maintainer_email = 'support@obsidianproject.co.uk',
      url='http://trac-hacks.org/wiki/LoomingCloudsPlugin',
      keywords='trac plugin',
      license = \
    """Copyright (c), Jeff Hammel. Copyright (c) 2010 Rowan Wookey. All rights reserved. Released under the 3-clause BSD license. """,
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data = {'loomingclouds' : ['htdocs/js/*.js', 'htdocs/css/*.css']}, 
      zip_safe=False,
      install_requires=['TracTags'],
      dependency_links=['http://trac-hacks.org/svn/tagsplugin/tags/0.6#egg=TracTags'],
      entry_points = """
      [trac.plugins]
      loomingclouds = loomingclouds
      """,
      )


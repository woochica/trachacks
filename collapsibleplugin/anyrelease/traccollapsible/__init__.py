#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#   Copyright 2010 Matthew Noyes <thecodingking at gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


r"""
Easily create foldable text structures in the style of trac ticket attachments

Copyright 2010 Matthew Noyes <thecodingking at gmail.com> 
Licensed under the Apache License
"""
__author__ = 'Matthew Noyes'

# Ignore errors to avoid Internal Server Errors
from trac.core import TracError
TracError.__str__ = lambda self: unicode(self).encode('ascii', 'ignore')

try:
    from traccollapsible.collapsible import *
    msg = 'Ok'
except Exception, exc:
#    raise
    msg = "Exception %s raised: '%s'" % (exc.__class__.__name__, str(exc))

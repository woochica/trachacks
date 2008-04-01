#!/usr/local/bin/python
#
#Copyright (c) 2008, Philippe Monnaie <philippe.monnaie@gmail.com>
#
#Permission to use, copy, modify, and/or distribute this software for any
#purpose with or without fee is hereby granted, provided that the above
#copyright notice and this permission notice appear in all copies.
#
#THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from trac.wiki.macros import WikiMacroBase
from trac.util import TracError

class PageVariable(WikiMacroBase):
	"""
	PageVariable macro.
	This macro sets or gets a variable that is accessible throughout the entire page.
	
	Use: [[PageVariable(name,value)]]
	Name signifies the name of the parameter.
	Value signifies the value the parameter should be set to. 
	If a value is supplied, this macro returns an empty string. When trying to set a variable that is already set (or present in the 		url for some other reason), an error is raised.
	If the parameter value is ommitted, the currently known value is returned. If no value is known, an error is raised.
	"""

    def expand_macro(self, formatter, name, args):
	self.req = formatter.req
	if len(args) == 1:
		return getValue(args[0])
	else: 
		if len(args) == 2:
			setValue(args[0],args[1])
			return ''
		else:
			return 'ERROR: Invalid number of arguments supplied to PageVariable macro: ' + str(args)
    
	def getValue(self, name):
		if hasattr(self.req,name):
			return self.req.name
		else:
			return 'ERROR: Variable ' +name+ ' not declared'

	def setValue(self, name,value):
		if hasattr(self.req,name):
			return 'ERROR: Variable ' +name+ ' already set or present in the url'
		else:
			self.req.name = value

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

from trac.util import TracError
import re

"""
GetPageVariable macro.
This macro gets a variable that is set by the SetPageVariable macro.
	
Use: [[GetPageVariable(name,text)]]
Name signifies the name of the parameter.
Text signifies the text the parameter is to be inserted in. The placement of the variable is signified by ${name}. ''[['' or '']]'' cannot be entered any field of the macro because it interferes with the interpreting of macros. To make it possible to enter special characters, the GetPageVariable allows escaping characters in the text parameter with a ''\''. Any character preceded by a ''\'' will be interpreted as just that character, ''\'' is represented by ''\\''. Take note that \${name} will still be replaced by the variable's value and will escape the first character of that value.
If the parameter text is ommitted, just the value of the variable is returned. 
If no value is known, an error is raised.
"""
def execute(hdf, args, env):
	arguments = args.split(',')
	if len(arguments) == 1:
		return getValue(hdf,arguments[0])
	else: 
		if len(arguments) == 2:
			result = re.sub(r'\$\{'+arguments[0]+r'\}',testValue, arguments[1])
			escapes = re.findall(r'\\.',result)
			for escape in escapes:
				result = re.sub('\\\\\\' + escape[1],escape[1],result)
			return result
		else:
			return 'ERROR: Invalid number of arguments supplied to PageVariable macro: ' + str(arguments)

def getValue(hdf,name):
	if hdf.has_key(name):
		return hdf[name]
	else:
		return 'ERROR: Variable ' +name+ ' not declared'

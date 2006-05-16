"""
small macro to fold areas and toggle the visibility on click.
first parameter is one of the following actions
    "printscript" prints the necessary javascript
    "begin" marks the beginning of the area to be folded
    "end" marks the end of the area to be folded
    "activator" prints the area that will activate the folding
second parameter is the id of the area to be folded/unfolded
third parameter can be
    "visibility" of the area when the action is "begin" (possible values "inline","none")        
    "formatting" of the content when the action is "activator" (possible values "wiki","none")
forth paramerter is the content for the activator action.

example usage:
[[Folding(printscript)]]

[[Folding(activator,idoftheregiontobeunfolded,wiki,== click me to view ==)]]
[[Folding(begin,idoftheregiontobeunfolded,none)]]
this area is folded by default
[[Folding(end)]]

[[Folding(activator,idoftheregiontobefolded,none,&lt;h2&gt;click me to hide&lt;/h2&gt;)]]
[[Folding(begin,idoftheregiontobefolded,inline)]]
this area is visible by default
[[Folding(end)]]

Author: Thorsten Ott (wanagi at web-helfer.de)
"""

from trac import util
from trac.wiki import wiki_to_html
from StringIO import StringIO
import os
import urllib

def execute(hdf, args, env):
	# Args seperated by commas:
	# url, formatter
	#
	# url is the url to go get.
	# Formatter is which formatter if any to parse.	 Default: None
	_href = env.abs_href or env.href
	formatter = None
	action = None
	id = None
	parameter = None
	db = env.get_db_cnx()
	cursor = db.cursor()
	cs = db.cursor()
	buf = StringIO()

	currentpage =  hdf.getValue('wiki.page_name', '') + '/'
	if args:
		args = args.replace('\'', '\'\'')
	args = args.split(',')
	if args[0] != 'None':
		action = args[0]
	try:	
		if args[1] != 'None':
			id = args[1]
	except:
		id = '';
	
	try:
		if args[2] != 'None':
			parameter = args[2]
	except:
		if action == 'begin': 
			parameter = 'inline'
		if action == 'activator':
			parameter = 'wiki'

	try: 	
		if args[3] != 'None':
			content = args[3]
	except:
		content = ''

	if action == 'printscript':
		output = '<script type=\'text/javascript\'>function switchMenu(obj) { var el = document.getElementById(obj); if ( el.style.display == \'none\' ) { el.style.display =\'inline\'; } else { el.style.display = \'none\'; } } </script>';
	
	if action == 'begin':
		output = '<span id="'+id+'" style="display: '+parameter+'">';
	if action == 'end':
		output = '</span>';
	
	if action == 'activator':
		if parameter == 'wiki':
			content = wiki_to_html(content,env,hdf,db,0)
		output = '<span onClick="javascript: switchMenu(\''+id+'\');">'+content+'</span>'
	
	buf.write(output)
	return buf.getvalue()

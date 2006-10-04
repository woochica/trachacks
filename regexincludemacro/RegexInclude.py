"""
We take an argument which is a file to go get.	The second argument is going to be None, or wiki at this point.

do we include it, and then parse it thru the wiki formatter or not?

url, can be a special case 'trunk' and it will grab from the local svn repository.

a couple of examples:

This will do no formatting on the url.
[[Include(http://www.yuma.ca/tech/license.html,None)]]

This will get the url, and do the Trac wiki formatting on it.
[[Include(http://www.yuma.ca/tech/license.html,wiki)]]

This will get the file out of the local SVN Repository(latest revision only).
[[Include(trunk/needs_document/Employee/employee_file.txt,wiki)]]

Theoretically you can modify this to handle more formatters, but I haven't the need so I stopped.

If you include Arguments, you MUST include both.  Sorry I'm lazy.

"""

from trac import util
from trac.wiki import wiki_to_html
from StringIO import StringIO
import os
import urllib
import re

def execute(hdf, args, env):
	# Args seperated by commas:
	# url, formatter
	#
	# url is the url to go get.
	# Formatter is which formatter if any to parse.	 Default: None
	_href = env.abs_href or env.href
	formatter = None
	url = None
	regex = None
	db = env.get_db_cnx()
	cursor = db.cursor()
	cs = db.cursor()
	buf = StringIO()

	currentpage =  hdf.getValue('wiki.page_name', '') + '/'
	if args:
		# Get regex's - last argument
		regex = re.search('^(?:.+?,)+?(\'.*)',args).group(1)
		args = args.replace('\'', '\'\'')

	#Split args
	args = args.split(',')
	regex = regex.split('\';\'')

	#Get URL
	if args[0] != 'None':
		url = args[0]
	#Get formatter
	if args[1] != 'None':
		formatter = args[1]	
	if url[:5] == 'trunk':
		# we need to get the file from the svn repo.
		#http://financial.trac.yumaed.org/trac.cgi/file/trunk/needs_document/Employee/employee_file.txt?format=raw
		url = 'http://' + os.getenv('HTTP_HOST') + env.href.base + '/file/' +  url + '?format=raw'
	if url[:7] != 'http://':
		#We are getting local file
		url = '/tmp/trac_include/' + url.replace('/','_');
		#url = 'http://' + os.getenv('HTTP_HOST') + env.href.base + '/file/' +  url + '?format=raw'
	try:
            f = urllib.urlopen(url)
        except:
            #raise util.TracError('The "%s" argument doesnt seem to be a valid link' % (args))
            raise util.TracError('The "%s" argument doesnt seem to be a valid link' % (url))
			#buf.write('<P>bad url: ')
			#buf.write(url)
	txt = f.read()
	
	#Regex replace
	re.DOTALL
	for ex in regex:
	        ex = ex.strip("'")
		ex = ex.split('\',\'')
		txt = re.sub(ex[0],ex[1],txt)
			
	if formatter == 'wiki':
		txt = wiki_to_html(txt,env,hdf,db,0)
	buf.write(txt)
	#buf.write(regex) #DEBUG
	return buf.getvalue()
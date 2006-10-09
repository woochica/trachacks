"""

I've added my own comments here. The original text is attached below my comments.
Also, please forgive any stupid errors i might have made. My i started on python 1 week ago.

use_vars: 
 Do we replace $USER with username?
 use_vars accepts an argument to change the case of the username which is one of:
 	upper
 	lower
 	ucfirst
 example:
 	use_vars=upper
 	 
 (note: ucfirst is "uppercase first letter only")
 

no_anon:
 Do not include this page for anonymous users. 
 NOTE: this is NOT a security feature, as anyone can still read your source code. 
 Good feature to not include unneseseary information for anon users. 


no_dotall:
 Disable the use of DOTALL option for regular expression. pr. default DOTALL is enabled
 and this make the dot (".") also include linebreaks.
 




-------ORIGINAL---------------
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
	argstring = ''
	match_seperator = ' '
	dotall = ''
	db = env.get_db_cnx()
	cursor = db.cursor()
	cs = db.cursor()
	buf = StringIO()

	currentpage =  hdf.getValue('wiki.page_name', '') + '/'
	if args:
		# Get regex's - last argument
		try:
		   regex = re.search('^(?:.+?,)+?(\'.*)',args).group(1)
		except:
		   regex =''

		argstring = argstring.join([',',args,',']) #Add trailing and tailing comma for easy matching
		args = args.replace('\'', '\'\'') 

	#Split args
	
	args = args.split(',')
        if regex != '':	
		regex = regex.split('\',\'')


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
	if (url[:7] != 'http://') and (url[:5] != 'wiki:'):
		#We are getting local file
		url = '/tmp/trac_include/' + url.replace('/','_');
		#url = 'http://' + os.getenv('HTTP_HOST') + env.href.base + '/file/' +  url + '?format=raw'

        authname = hdf.getValue("trac.authname", "anonymous")
	# control options
        #------------------------
	#If arg no_dotall is set, disable DOTALL usage
	try:
	   argstring.index(',no_dotall,')
	except:
	   re.DOTALL #Aparantly this doesnt always work..
	   dotall = '(?s)' # So we use this regex equivilant
	   #buf.write('DOTALL')
	
	#Should we only include pages for authenticated users?
	try:
	   argstring.index(',no_anon,')
	   if authname == "anonymous":
	   		return buf.getvalue()
	except:
	  1 #Sorry.. Dont know python at all, and this was the only way i could solve that except: requires at least 1 line
	#Should we only include pages for authenticated users?

        if re.search(',match_seperator(?:=[^,]+)?,',argstring):
              match_seperator = re.search(',match_seperator(?:=([^,]+))?,',argstring).group(1)

        #Or allow the match seperator to be in quotes
        if re.search(',match_seperator="[^"]+?"?,',argstring):
              match_seperator = re.search(',match_seperator="([^"]+?)"?,',argstring).group(1)
              
              
              
	#Should we replace $USER with logged-in username, in URL?
        if re.search(',use_vars(?:=\w+)?,',argstring):
              sub_arg = re.search(',use_vars(?:=(\w+))?,',argstring).group(1)
              if sub_arg == 'lower':
			authname = authname.lower()
              if sub_arg == 'upper':
			authname = authname.upper()
              if sub_arg == 'ucfirst': 
			authname = authname.capitalize()
              		
  	      url = url.replace('$USER',authname)
	#-----------------------------


        #Fetch the included page
        if url[:5] == 'wiki:': #Wiki url
		url = url[5:]

                sql = "SELECT text from wiki where name = '%s' order by version desc limit 1" % url
        	cs = db.cursor()
        	cs.execute(sql)

        	row = cs.fetchone()
        	if row == None:
                	return ''
        	txt = row[0]
        else: # Normal URL
		try:
			f = urllib.urlopen(url)
		except:
			raise util.TracError('The "%s" argument doesnt seem to be a valid link' % (url))
		txt = f.read()
	
	#Do the regex replacements
	for ex in regex:
		#Detect replace or search
		ex = ex.strip("'")
		
		try: 
		        ex.index("'/'") #Check If this is a replacement
	        	ex = ex.split('\'/\'')
        		txt = re.sub(dotall+ex[0],ex[1],txt)
		except: #If this is a search
			tmp = ''
			for m in re.finditer(dotall+ex, txt):
				tmp = "".join([tmp,match_seperator,m.group(1)])
			txt = tmp[1:]
		
			
	if formatter == 'wiki':
		txt = wiki_to_html(txt,env,hdf,db,0)
	buf.write(txt)
#	buf.write(env) #DEBUG
	return buf.getvalue()

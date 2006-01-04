#! /usr/bin/env python

# Trac plugin framework generator
# Usage: newegg.py [options] name [url]

from optparse import OptionParser
from string import Template
import os
import sys
	
usage = "%prog [options] name [url]"
version = "%prog 1.0"
parser = OptionParser(usage=usage,version=version)
parser.add_option('-t','--template',action='store_true',default=False, help='Adds template support to the skeleton')
parser.add_option('-s','--stylesheet',action='store_true',default=False, help='Adds stylesheet support to the skeleton')
parser.add_option('-i','--image',action='store_true',default=False, help='Adds image support to the skeleton')
parser.add_option('-p','--pretend',action='store_true',default=False, help='Don\'t do anything, but show what would have been done')
(opts, args) = parser.parse_args()
if len(args) == 0:
	parser.error('No name argument passed')
elif len(args) == 1:
	name = url = args[0]
else:
	name = args[0]
	url = args[1]

# Stuff for --pretend
if opts.pretend:
	def replace_fn(fn):
		def make_fn(fn):
			def show(x):
				print x
			return lambda *args: show('Got %s(%s)' % (fn,','.join([str(arg) for arg in args])))
		exec "%s = make_fn('%s')" % (fn,fn) in globals(),locals()
	def replace_mod(mod):
		for fn in ['%s.%s'%(mod,fn) for fn in dir(eval(mod)) if callable(eval(mod+'.'+fn))]:
			replace_fn(fn)
	replace_mod('os')

	class fake_file:
		def __init__(self, name):
			self.name = name
		def write(self,*args):
			print "Writting %s\n<<<<<\n%s>>>>>" % (self.name,''.join(args))
		def close(self):
			print "Closing %s" % self.name
	def myopen(file,mode):
		print "Opening %s in mode %s" % (file,mode)
		return fake_file(file)
	open = myopen

# Make the needed directories
os.mkdir(name+'-plugin')
os.chdir(name+'-plugin')
os.mkdir(name)
os.mkdir(name.capitalize()+'.egg-info')
if opts.template:
	os.mkdir(name+'/templates')
if opts.stylesheet:
	os.makedirs(name+'/htdocs/css')
if opts.image:
	os.makedirs(name+'/htdocs/images')

# Write the module load skeleton
file = open(name+'/__init__.py','w')
file.write("# %s module\nfrom %s import *\n" % (name.capitalize(),name))
file.close()

# Write the trac_plugin file
file = open(name.capitalize()+'.egg-info/trac_plugin.txt','w')
file.write(name+"\n")
file.close()

# Generate the setup.py
setuppy = """from setuptools import setup

PACKAGE = '%s'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION, packages=['%s']""" % (name.capitalize(),name) 

if opts.template or opts.stylesheet or opts.image:
	setuppy += """,
        package_data={'%s' : [""" % name
	if opts.template:
		setuppy += "'templates/*.cs', "
	if opts.stylesheet:
		setuppy += "'htdocs/css/*.css', "
	if opts.image:
		setuppy += "'htdocs/images/*.jpg', 'htdocs/images/*.png', 'htdocs/images/*.gif', "
	setuppy = setuppy.rstrip(', ') # This will remove the trailing comma
	setuppy += "]}"
setuppy += ")\n"

file = open('setup.py','w')
file.write(setuppy)
file.close()

# Write the main file
mainpy = Template("""# $cname plugin

from trac.core import *
from trac.web.chrome import $chromeimps
from trac.web.main import IRequestHandler
from trac.util import escape

class ${cname}Plugin(Component):
    implements($imps, IRequestHandler)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return '$name'
                
    def get_navigation_items(self, req):
        yield 'mainnav', '$name', '<a href="%s">$cname</a>' \\
                                  % escape(self.env.href.$url())

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/$url'
    
    def process_request(self, req):
""").substitute({'name':name, \
       'cname':name.capitalize(), \
       'url':url, \
       'chromeimps': ('INavigationContributor'+('',', ITemplateProvider')[opts.template or opts.stylesheet or opts.image]+('',', add_stylesheet')[opts.stylesheet]), \
       'imps': ('INavigationContributor'+('',', ITemplateProvider')[opts.template or opts.stylesheet or opts.image]) \
      })

if opts.stylesheet:
	mainpy += "        add_stylesheet(req, '%s/css/%s.css')\n" % (url, name)

if opts.template:
	mainpy += "        return '%s.cs', None\n" % name
else:
	mainpy += "        pass # Put your code here\n"

if opts.template or opts.stylesheet or opts.image:
	mainpy += "\n    # ITemplateProvider methods\n"

if opts.template:
	mainpy += """    def get_templates_dirs(self):
        \"""
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        \"""
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

"""

if opts.stylesheet or opts.image:
	mainpy += """    def get_htdocs_dirs(self):
        \"""
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        \"""
        from pkg_resources import resource_filename
        return [('%s', resource_filename(__name__, 'htdocs'))]

""" % url

file = open(name+'/'+name+'.py','w')
file.write(mainpy)
file.close()

# Template skeleton
if opts.template:
	file = open(name+'/templates/'+name+'.cs','w')
	file.write("""<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="%s">
<!-- Your content here --->
</div>

<?cs include "footer.cs" ?>
""" % name)
	file.close()

# CSS skeleton
if opts.stylesheet:
	file = open(name+'/htdocs/css/'+name+'.css','w')
	file.write("/* Your CSS goes here */\n")
	file.close()

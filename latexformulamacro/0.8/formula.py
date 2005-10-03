"""
Convert a latex formula into an image.
by Valient Gough <vgough@pobox.com>

Changes:
    2005-09-21:
	* add #center and #indent options to add html formatting around image.
    2005-08-02:
	* remove hard-coded paths, read from configuration. Fixes #26
    2005-07-27:
	* figured out how to get rid of the annoying internal error after latex
	was run.  Redirected latex output to /dev/null..
	* found out that {{{#!figure ... }}} runs wiki macro, and doesn't have
	the problem of not being able to use paranthesis.  So this is the
	default usage now.  Can still use [[formula(...)]] for simple formula.
	* add "nomode" command, which can be used to turn off automatic
	  enclosure of commands in display-math mode ("$$ ... $$")
    2005-07-26: first release

Installation:
    1. Copy into wiki-macros directory.
    2. Edit conf/trac.ini and add a [latex] group with three values:
	[latex]
	# temp_dir points to directory where temporary files are created
	temp_dir = /var/tmp/trac
	# image_path is directory where final images are written
	image_path = /var/www/html/formula
	# display_path is URL where formula images can be accessed
	display_path = http://foo.net/formula

Usage:

{{{
#!formula
[latex code]
}}}

or, additional keywords can be specified before the latex code:
{{{
#!formula
#density=100
[latex code]
}}}

Optional keywords (must be specified before the latex code):
    #density=100
	Density defaults to 100.  Larger values produces larger images.
    #nomode
	Disable the default display mode setting.  Use this if you want to
	include things outside of tex's display mode.	
    #center
	Center image on the page.
    #indent [=class name]
	places image link in a paragraph <p>...</p>
	If class name is specified, then it is used to specify a CSS class for
	the paragraph.

Notes:
    A matrix macro is included in the tex code.  This allows you to do things
    like:
      \mat{1&2\\3&4}  to get a 2x2 matrix.  The "\\" separates rows, and "&"
      separates columns.  Any size up to around 25? will work..

Images are automatically named based on a sha1 hash of the formula, the
density, and the script version.  This way the image doesn't have to be
regenerated every time it is used, and if anything is changed then a new image
is created.

Note that temporary files can build up in the tmpdir, and every time a formula
is modified, a new image will be created in the imagePath directory.  These can
be considered as cached files.  You can safely let the tmp file cleaner process
remove old files from these directories.

PS.  This is my first python program, so it is probably pretty ugly by python
standards (whatever those may be).  Feedback is welcome, but complaints about
ugliness will be redirected to /dev/null.
"""

# if the output version string changes, then images will be regenerated
outputVersion = "0.1"


import re
import string
import os
import sha


def render(hdf, env, texData, density, mathMode):
    # gets paths from configuration
    tmpdir = env.get_config('latex', 'temp_dir')
    imagePath = env.get_config('latex', 'image_path')
    displayPath = env.get_config('latex', 'display_path')

    if not tmpdir or not imagePath or not displayPath:
	return "<b>Error: missing configuration settings in 'latex' macro</b><br>"

    path = tmpdir # + hdf.getValue("project.name.encoded", "default")
    # create temporary directory if necessary
    try:
	if not os.path.exists(path):
	    mkdir(path)
    except:
	return "Unable to create temporary directory " + path
    
    # generate final image name.  Use a hash of the parameters which affect
    # the image, so we don't have to recreate it unless they change.
    hash = sha.new(texData)
    hash.update( "%d" % density )
    hash.update( outputVersion )
    name = hash.hexdigest()
    jpgFile = "%s/%s.jpg" % (imagePath, name)

    log = "<br>"
    if not os.path.exists(jpgFile):
	# latex writes out lots of stuff to the current directory, so we have
	# to run it from there.
	cwd = os.getcwd()
	os.chdir(path)

	texFile = name + ".tex"
	makeTexFile(texFile, texData, mathMode)

	# the output from latex on stdout seems to cause problems, so sent it
	# to /dev/null
	cmd = "latex %s > /dev/null" % texFile
	log += execprog( cmd )
	os.chdir(cwd)

	# use dvips to convert to eps
	dviFile = "%s/%s.dvi" % (path, name)
	epsFile = "%s/%s.eps" % (path, name)
	cmd = "dvips -q -D 600 -E -n 1 -p 1 -o %s %s" % (epsFile, dviFile)
	log += execprog( cmd )

	# and finally, ImageMagick to convert from eps to jpg
	cmd = "convert -antialias -density %ix%i %s %s" % (density, density, epsFile, jpgFile)
	log += execprog( cmd )

    html = "<img src='%s/%s.jpg' border='0' style='vertical-align: middle;' alt='formula' />" % (displayPath, name)
    return html

def execprog(cmd):
    os.system( cmd )
    return cmd + "<br>"

def makeTexFile(texFile, texData, mathMode):
    tex = "\\batchmode\n"
    tex += "\\documentclass{article}\n"
    tex += "\\usepackage{epsfig}\n"
    tex += "\\pagestyle{empty}\n"
    # matrix macro
    tex += "\\newcommand{\\mat}[2][rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr]{\n"
    tex += "  \\left[\\begin{array}{#1}\n"
    tex += "  #2\\\\\n"
    tex += "  \\end{array}\n"
    tex += "  \\right]}\n"
    # start the document
    tex += "\\begin{document}\n"
    if mathMode:
	tex += "$$\n"
    tex += "%s\n" % texData
    if mathMode:
	tex += "$$\n"
    tex += "\\pagebreak\n"
    tex += "\\end{document}\n"
	
    FILE = open(texFile, "w")
    FILE.write( tex )
    FILE.close()

# arguments start with "#" on the beginning of a line
def execute(hdf, text, env):
    # TODO: unescape all html escape codes
    text = text.replace("&amp;", "&")
    
    # defaults
    density = 100
    mathMode = 1 #default to using display-math mode
    centerImage = 0
    indentImage = 0
    indentClass = ""

    # find some number of arguments, followed by the formula
    command = re.compile('^#([^=]+)=?(.*)')
    formula = ""
    errors = ""
    for line in text.split("\n"):
	m = command.match(line)
	if m:
	    if m.group(1) == "density":
		density = int(m.group(2))
	    elif m.group(1) == "nomode":
		mathMode = 0
	    elif m.group(1) == "center":
		centerImage = 1
	    elif m.group(1) == "indent":
		indentImage = 1
		indentClass = m.group(2)
	    else:
		errors = '<br>Unknown <i>formula</i> command "%s"<br>' % m.group(1)
	else:
	    formula += line + "\n"

    format = '%s'
    if centerImage:
	format = '<center>%s</center>' % format
    if indentImage:
	if indentClass:
	    format = '<p class="%s">%s</p>' % (indentClass, format)
	else:
	    format = '<p>%s</p>' % format
    
    result = errors + render(hdf, env, formula, density, mathMode) 
    return format % result


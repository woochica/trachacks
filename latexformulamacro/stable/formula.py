"""
Convert a latex formula into an image.
by Valient Gough <vgough@pobox.com>

Usage:  [[formula([density|] latex-formula )]]
    Density defaults to 100.  Larger values produces larger images.
    Density is optional, but if it is include, it must be included first.

Images are automatically named based on a sha1 hash of the formula, the
density, and the script version.  This way the image doesn't have to be
regenerated every time it is used, and if anything is changed then a new image
is created.

Note that temporary files can build up in the tmpdir, and every time a formula
is modified, a new image will be created in the imagePath directory.  These can
be considered as cached files.  You can safely let the tmp file cleaner process
remove old files from these directories.

PS.  This is my first python program, so it is probably pretty ugly by python
standards (whatever those may be).
"""

# TODO: Paths to change for your system:
# directory where temporary files are created
tmpdir = "/tmp/trac-tex/"
# directory where images are written
imagePath = "/var/www/html/figures/"
# URL base for accessing images
displayPath = "http://arg0.net/figures/"

# if the version string changes, then images will be regenerated
version = "0.1"


import re
import string
import os
import sha


def render(hdf, env, texData, density):
    path = tmpdir # + hdf.getValue("project.name.encoded", "default") + "/"
    # create temporary directory if necessary
    try:
	if os.path.exists(path) is False:
	    mkdir(path)
    except:
	return "Unable to create temporary directory " + path
    
    # generate final image name.  Use a hash of the parameters which affect
    # the image, so we don't have to recreate it unless they change.
    hash = sha.new(texData);
    hash.update( "%d" % density )
    hash.update( version )
    name = hash.hexdigest()
    jpgFile = imagePath + name + ".jpg"

    log = "<br>";
    if os.path.exists(jpgFile) is False:
	# latex writes out lots of stuff to the current directory, so we have
	# to run it from there.
	cwd = os.getcwd()
	os.chdir(path)

	texFile = name + ".tex"
	makeTexFile(texFile, texData)

	cmd = "latex %s" % texFile
	# TODO: this causes error, even though the command appears to run to
	# completion
	log += execprog( cmd )
	os.chdir(cwd)

	# use dvips to convert to eps
	dviFile = path + name + ".dvi"
	epsFile = path + name + ".eps"
	cmd = "dvips -q -D 600 -E -n 1 -p 1 -o %s %s" % (epsFile, dviFile)
	log += execprog( cmd )

	# and finally, ImageMagick to convert from eps to jpg
	cmd = "convert -antialias -density %ix%i %s %s" % (density, density, epsFile, jpgFile)
	log += execprog( cmd )

    html = "<img src='%s%s.jpg' border='0' style='vertical-align: middle;' alt='formula' />" % (displayPath, name)
    return html
    #return log;

def execprog(cmd):
    os.system( cmd )
    return cmd + "<br>"

def makeTexFile(texFile, texData):
    tex = "\\batchmode\n"
    tex += "\\documentclass{article}\n"
    tex += "\\usepackage{epsfig}\n"
    tex += "\\pagestyle{empty}\n"
    tex += "\\newcommand{\\mat}[2][rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr]{\n"
    tex += "  \\left[\\begin{array}{#1}\n"
    tex += "  #2\\\\\n"
    tex += "  \\end{array}\n"
    tex += "  \\right]}\n"
    tex += "\\begin{document}\n"
    tex += "$$\n"
    tex += "%s\n" % texData
    tex += "$$\n"
    tex += "\\pagebreak\n"
    tex += "\\end{document}\n"
	
    FILE = open(texFile, "w")
    FILE.write( tex )
    FILE.close()

# first argument is the image name, second argument is the formula
def execute(hdf, text, env):
    args = text.split('|') 
    if len(args) < 1 or len(args) > 2:
	return "Usage: [[formula([density|] tex-data)]]\n"

    # defaults
    density = 100
    if len(args) == 1:
	formula = args[0]
    elif len(args) == 2:
	density = int(args[0])
	formula = args[1]

    return render(hdf, env, formula, density) 



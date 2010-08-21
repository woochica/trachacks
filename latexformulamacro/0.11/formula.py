"""
Convert a latex formula into an image.
by Valient Gough <vgough@pobox.com>, David Douard <david.douard@gmail.com>

Changes:
	2008-02-17: Boris Resnick <boris@resnick.ru>:
		* make this macro work with Trac 0.11
		* make it run under Windows NT family
    2006-01-16 (David Douard):
        * make this macro work with Trac 0.9
        * make the generated images be saved in $PROJECT/htdocs/formulas
        * make default image format be 'png'
        * replaced every Tab by spaces
        * make tmp dir creation recursive 
    2005-10-21:  Ken McIvor <mcivor@iit.edu>:
        * Updated to support trac 0.9b2.
        * Improved the error messages for missing configuration elements.
    2005-10-03:
        * make image format selectable via 'image_format' configuration option
          (defaults to 'jpg')
        * allow paths to executables to be specified in configuration by
          setting 'latex_path', 'dvips_path', 'convert_path' to point to
          executable. Based on code by Reed Cartwright.
    2005-10-01:
        * add #display and #fleqn options to add html formatting around image
          (Christian Marquardt).
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
        # Set to 1 for fleqn style equations (default is centered)
        fleqn = 0
        # Indentation width for fleqn style equations
        fleqn_width = '5%'

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
    #display
        Create a displayed equation (either centered or fleqn style,
        depending on the fleqn variable in the config file.
    #center
        Center the equation on the page.
    #fleqn
        fleqn style equation; indentation is controlled by fleqn_witdh in
        conf/trac.ini.
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

from trac.wiki.macros import WikiMacroBase

revison = "$Rev$"
url = "$URL$" 

def render(env, texData, density, fleqnMode, mathMode):
    # gets paths from configuration
    tmpdir = env.config.get('latex', 'temp_dir')

    cfg = env.config
    fleqnIndent = cfg.get('latex', 'fleqn_indent', '5%')
    latexPath = cfg.get('latex', 'latex_path', 'latex')
    dvipsPath = cfg.get('latex', 'dvips_path', 'dvips')
    convertPath = cfg.get('latex', 'convert_path', 'convert')
    texMag = cfg.get('latex', 'text_mag', 1000)
    imageFormat = cfg.get('latex', 'image_format', 'png')

    imagePath = os.path.normpath(os.path.join(env.get_htdocs_dir(), "formulas"))
    if not os.path.exists(imagePath):
        try:
            os.mkdir(imagePath)
        except:
            return "<b>Error: unable to create image directory</b><br>"        

    def make_cfg_error(element):
	msg = """\
<div class="system-message">
    <strong>Error: the <code>formula</code> macro requires the
	setting <code>%s</code> in the configuration section
	<code>latex</code>
    </strong>
</div>
"""
	return msg % element

    if not tmpdir:
	return make_cfg_error('temp_dir')
    if not imagePath:
	return make_cfg_error('image_path')

    path = tmpdir
    # create temporary directory if necessary
    def mkd(path):
        if not os.path.exists(path):
            d, t, = os.path.split(path)
            if not os.path.exists(d):
                mkd(d)
            
            os.mkdir(path)
                 
    try:
        if not os.path.exists(path):
            mkd(path)
    except:
        return "Unable to create temporary directory " + path
    
    # generate final image name.  Use a hash of the parameters which affect
    # the image, so we don't have to recreate it unless they change.
    hash = sha.new(texData)
    # include some options in the hash, as they affect the output image
    hash.update( "%d %d" % (density, int(texMag)) ) 
    hash.update( outputVersion )
    name = hash.hexdigest()
    imageFile = "%s/%s.%s" % (imagePath, name, imageFormat)

    log = "<br>"
    if not os.path.exists(imageFile):
        # latex writes out lots of stuff to the current directory, so we have
        # to run it from there.
        cwd = os.getcwd()
        os.chdir(path)

        texFile = name + ".tex"
        makeTexFile(texFile, texData, mathMode, texMag)

        # the output from latex on stdout seems to cause problems, so sent it
        # to /dev/null (or NUL under Windows)
	if os.name == "nt":
            nullDevice = "nul"
	else:
	    nullDevice = "/dev/null"

	cmd = "%s %s > %s" % (latexPath, texFile, nullDevice)
        log += execprog( cmd )
        os.chdir(cwd)

        # use dvips to convert to eps
        dviFile = "%s/%s.dvi" % (path, name)
        epsFile = "%s/%s.eps" % (path, name)
        cmd = "%s -q -D 600 -E -n 1 -p 1 -o %s %s" % (dvipsPath, epsFile, dviFile)
        log += execprog( cmd )

        # and finally, ImageMagick to convert from eps to [imageFormat] type
        cmd = "%s -antialias -density %ix%i %s %s" % (convertPath, density, density, epsFile, imageFile)
        log += execprog( cmd )

    if fleqnMode:
        margin = " margin-left: %s" % fleqnIndent
    else:
        margin = ""
        
    html = "<img src='%s' border='0' style='vertical-align: middle;%s' alt='formula' />" % (env.href.chrome('site','formulas/%s.%s'%(name, imageFormat)), margin)
    # Uncomment this for debugging purposes
    #html += "<h1>log</h1>"
    #html += log

    return html

def execprog(cmd):
    os.system( cmd )
    return cmd + "<br>"

def makeTexFile(texFile, texData, mathMode, texMag):
    tex = "\\batchmode\n"
    tex += "\\documentclass{article}\n"
    tex += "\\usepackage{amsmath}\n"
    tex += "\\usepackage{amssymb}\n"
    tex += "\\usepackage{epsfig}\n"
    tex += "\\pagestyle{empty}\n"
    tex += "\\mag=%s\n" % texMag
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
def execute(text, env):
    cfg = env.config

    # TODO: unescape all html escape codes
    text = text.replace("&amp;", "&")
        
    # defaults
    density = 100
    mathMode = 1    # default to using display-math mode for LaTeX processing
    displayMode = 0 # default to generating inline formula
    fleqnMode   = cfg.get('latex', 'fleqn')
    centerImage = 0
    indentImage = 0
    indentClass = ""

    # find some number of arguments, followed by the formula
    command = re.compile('^\s*#([^=]+)=?(.*)')
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
                fleqnMode   = 0
            elif m.group(1) == "indent":
                indentImage = 1
                indentClass = m.group(2)
            elif m.group(1) == "display":
                displayMode = 1
            elif m.group(1) == "fleqn":
                displayMode = 1
                fleqnMode   = 1
            else:
                errors = '<br>Unknown <i>formula</i> command "%s"<br>' % m.group(1)
        else:
            formula += line + "\n"

    # Set display and fleqn defaults
    if displayMode:
	if fleqnMode:
	    centerImage = 0
	else:
	    centerImage = 1

    # Render formula
    format = '%s'
    if centerImage:
	format = '<center>%s</center>' % format
    if indentImage:
	if indentClass:
	    format = '<p class="%s">%s</p>' % (indentClass, format)
	else:
	    format = '<p>%s</p>' % format
    
    result = errors + render(env, formula, density, fleqnMode, mathMode) 
    return format % result

class formulaMacro(WikiMacroBase):
    
    def expand_macro(self, formatter, name, args):
        return execute(args, self.env)

"""
The MIT License

Copyright (c) 2009 James Cooper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from trac.util import escape
from trac.core import TracError
import urllib
import gliffylib
import os
import sys

#
# Gliffy trac plugin
#
# Usage:
#
#   1) put this file, oauth.py, and gliffylib.py in your "$TRAC/wiki-macros" dir
#   2) Add a [gliffy] block to your trac.ini with these keys:
#        [gliffy]
#        consumer_key = aaaaaaaaaaa
#        consumer_secret = zzzzzzzzzzzz
#        account_id = 1234
#        username = yourgliffyuser@example.com
#
#   3) edit a trac wiki page and add a macro.  example:
#
#          [[GliffyDiagram(Test Doc 2|ROOT/myfolder)]]
#
#      Format is:  [[GliffyDiagram(filename|folder path|type|size)]]
#
#           filename -- name of doc to edit. required. if doc doesn't exist it will be created
#        folder path -- folder path.  optional.  folder must exist - it won't be created
#                       ROOT/ is important -- all subfolders exist under ROOT/ by default
#               type -- png, jpg, svg, xml -- format to return image as.  optional. default is png.
#               size -- T, S, M, L         -- size of image to return.  optional.  default is M.
#
def execute(hdf, args, env):
    if hdf:
        hdf['wiki.macro.greeting'] = 'Gliffy Diagram'
        
    args = args.split('|')
    docName    = args[0]
    folderPath = None
    type       = 'png'
    size       = 'M'
    if len(args) > 1:
        folderPath = args[1]
    if len(args) > 2:
        type = args[2]
    if len(args) > 3:
        size = args[3]
        
    returnUrl = 'http://' + os.environ['HTTP_HOST'] + env.href.base + os.environ['PATH_INFO']

    consumer_key    = getConfig(env, 'consumer_key')
    consumer_secret = getConfig(env, 'consumer_secret')
    account_id      = getConfig(env, 'account_id')
    username        = getConfig(env, 'username')
    
    gliffy    = gliffylib.GliffyApi(consumer_key, consumer_secret, account_id, username)
    gliffy.login()
    docId     = gliffy.getOrCreateDocument(docName, folderPath)
    imageUrl  = gliffy.getImageUrl(docId, type, size)
    editorUrl = gliffy.getLaunchDiagramUrl(docName, returnUrl)

    text  = "<a href='%s'><img src='%s' border='0' /></a>" % (imageUrl, imageUrl)
    text += "<p><a href='%s'>Edit Diagram</a></p>" % editorUrl
    return text
    

def getConfig(env, key):
    val = env.config.get('gliffy', key)
    if val:
        return val
    else:
        raise TracError("Missing config value.  Section: [gliffy]  Property: %s" % key)

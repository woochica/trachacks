#! /usr/bin/env python
from trac.core import *
from trac.env import Environment
from trac.wiki.model import WikiPage
from tempfile import NamedTemporaryFile
import sys
import os
import pwd
import string

# Grab the arguments
name = sys.argv[1]
editor = os.environ['EDITOR']

# Open the envrionment
env = Environment('/var/trac/helpdesk')

# Grab the page model
page = WikiPage(env, name)

# Make a temporary file
safename = name.translate(string.maketrans('/','_'))
file = NamedTemporaryFile(mode='w+',prefix=safename,suffix='.txt')

# If the page exists, populate the tempfile
if page.exists:
    file.write(page.text)
    file.flush()
    
# Open the file in $EDITOR
os.spawnlp(os.P_WAIT,editor,editor,file.name)

# Reread the text
file.seek(0)
page.text = file.read()

# Save the file back
try:
    page.save(author=os.getlogin(), comment='', remote_addr='127.0.0.1')
    print 'Page changed succesfully'
except TracError, e:
    print 'Error: %s' % e.message

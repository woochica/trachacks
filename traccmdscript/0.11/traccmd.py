#!/usr/bin/python

# (C) Copyright WooMedia 2009

"""
Command line handling for trac integration.

Simple, obvious things you might want to do from the command line or
write simple scripts around.

== Authentication ==

trac obviously requires authentication. This program offers a simple,
but relatively secure option for authenticating.

running like this:

 ./traccmd.py shell username [trac_url]

will ask for a password and then create a subshell in which there is
an environment variable containing the authentcated trac url. You can
then use trac.py within that shell without further specifying auth.

When you're finished, you kill the shell and all record of the
environment variable (and your auth details) is gone.


=== Ini file authentication ===

If you don't want this level of security and are happy to store auth
details in ini files you can setup $TRAC_CMD_INI or ~/.trac_cmd.ini 
thusly:

{{{
[Auth]
trac_url = http://..../trac-project
username = yourtracusername
password = yourtracpassword
}}}

and it will be used as authentication of last resort.


== New tickets ==

You can make new tickets like so:

 ./trac.py ticketnew to summary tickettype component description

the description is wiki text. Here's an example:

 ~/traccmd.py ticketnew mikero \
                     'use the command line ticket tool' \
                     task \
                     admin \
       'Use my new command line ticket tool! You muppet!'

When a ticket has been created the ticket number is printed.


== Other commands ==

 * methods  - retrieves the xmlrpc methods available from trac;
              provide a regex to filter further
 * method   - shows help on the specified methods
 * wiki     - get the specified wiki page.
              The page is prefaced with an s-expression of attributes
 * wikiput  - update the specified wiki page with stdin
 * wikiedit - edit the specified page in $EDITOR  
 * ticket   - get the specified tickets.
 * ticketdetail
            - specify a ticket number and some detail types 
              and you'll get a list of those details.
 * ticketupdate
            - specify a ticketnumber, a field and a value and 
              traccmd will update your ticket.

Author: Nic Ferrier, nferrier@woome.com
"""

import re
import os
import sys
import xmlrpclib
from urllib import urlencode
import tempfile
from ConfigParser import ConfigParser
import pdb
import traceback

def _get_ini_file(section):
    """Read in the trac_cmd ini file and return a dict of the specified section"""
    trac_ini_file = os.environ.get("TRAC_INI", 
                                   "%s/.trac_cmd.ini" % os.environ["HOME"])
    if not os.path.exists(trac_ini_file):
        return {}
    try:
        fd = open(trac_ini_file)
        cp = ConfigParser()
        cp.readfp(fd)
        return dict(cp.items(section))
    except Exception, e:
        print >>sys.stderr, "reading the trac_cmd ini file failed because: %s" % str(e)
        return {}


## Authentication and "login" stuff

def _login_auth(username, password, trac_url):
    token = re.sub("(http[s]*)://(.*)", "\\1://%s:%s@\\2" % (username, password), trac_url)
    os.environ["TRAC_URL"] = token
    return os.environ["TRAC_URL"]
    
def _login(username=None, password=None, trac_url=None):
    """Do login filling in gaps from ini file if necessary"""
    auth_details = {
        "username": username, 
        "password": password, 
        "trac_url": trac_url
        }
    if None in auth_details.values():
        cfg_details = _get_ini_file("Auth")
        auth_details.update(cfg_details)
    return _login_auth(**auth_details)


def loginemacs(username, password, trac_url=None):
    """Return the environment settings for doing trac env in emacs"""
    print """(setenv "TRAC_URL" \"%s\")""" % _login(username, password, trac_url)
    
def shell(username, trac_url=None):
    """Make some script to export your username/password to your current session environment.

    Call this in your shell before using the other commands.

    It execs a new shell with your environment variable setup.

    Improvements: make this collect the password with a secret read.
    """
    import getpass
    password = getpass.getpass()
    _login(username, password, trac_url)
    os.execl(os.environ["SHELL"])


## RPC management 

def _get_trac_url():
    trac_url = os.environ.get("TRAC_URL", None)
    if not trac_url:
        return _login()
    return trac_url

def _get_xmlrpc():
    """Called by everything to actually do the login"""
    trac_url = _get_trac_url()
    xr = xmlrpclib.ServerProxy("%s/login/xmlrpc" % trac_url)
    return xr

## RPC exposure methods

def methods(*patterns):
    """Lists the xmlrpc methods available from trac."""
    matched = True
    server = _get_xmlrpc()
    for methName in server.system.listMethods():
        if patterns:
            matched = False
            for pat in patterns:
                matched = re.match(pat, methName)
        if matched:
            print methName

def method(*methnames):
    """Shows the documentation for the xmlrpc methods specified.
    More than 1 method may be specified.
    """
    server = _get_xmlrpc()
    for meth in methnames:
        print server.system.methodHelp(meth)

## Wiki handling methods

def wiki(page_name, version=None):
    """Simply retrieves the wiki page

    Prepends with an s-expression of page attributes."""

    server = _get_xmlrpc()
    print "(:tracwikiproperties ("
    for name,value in server.wiki.getPageInfo(page_name).iteritems():
        print ":%s \"%s\"" % (name,value)
    print "))"
    print server.wiki.getPage(page_name)

def wikiput(page_name, content=None):
    """Puts the page back to the wiki

    content is the page or "-" to indicate that the content is on
    stdin."""

    server = _get_xmlrpc()
    if content == None or content == "-":
        content = sys.stdin.read()
    server.wiki.putPage(page_name, content, {})

def wikiedit(page_name):
    """Simple operating system trac integration.

    Opens the page and calls $EDITOR on it, then puts the resulting page
    back to the wiki once you quit the editor."""

    server = _get_xmlrpc()
    content = server.wiki.getPage(page_name)
    filedesc, file_name = tempfile.mkstemp()
    fd = os.fdopen(filedesc, "w+")
    try:
        print >>fd, content
    except IOError:
        print >>sys.stderr, "couldn't write to a temp file for editing %s" % page_name
        sys.exit(1)
    else:
        fd.close()
        os.spawnlp(os.P_WAIT, os.environ["EDITOR"], os.environ["EDITOR"], file_name)
        try:
            fd = open(file_name)
            content = fd.read()
        except IOError:
            print >>sys.stderr, "couldn't read the new version of %s" % page_name
            sys.exit(1)
        else:
            fd.close()
            server.wiki.putPage(page_name, content, {})
            


## Ticket handling methods

def tickets(*args):
    """Alias for ticket(*args)"""
    ticket(*args)

def ticket(*tickets):
    """Produce output about each ticket specified"""

    def ticket_fmt(prefix, s):
        # Anti-charlie device
        # Sometimes he seems to add random unicode chars to strings
        # There is no rhyme or reason to this
        # We try and strip them out.
        if type(s) == type(u""):
            s=s.encode('ascii', 'replace')
        return re.sub("\n", "\n%s " % prefix, str(s))

    server = _get_xmlrpc()
    for t in tickets:
        # Force ticket input to a number
        m = re.match("#([0-9]+)", t)
        if m:
            t = m.group(1)

        ticket = server.ticket.get(t)
        attrs = ticket[3]
        for name,value in attrs.iteritems():
            try:
                print "%d %s %s" % (int(t), name, ticket_fmt("%d %s" % (int(t), name), value))
            except:
                print >>sys.stderr, "whoops! encoding problem"
        changelog = server.ticket.changeLog(t)
        for log in changelog:
            try:
                fmtdlines = []
                print u"%d %s" % (int(t), u" ".join(ticket_fmt(int(t), attrib) for attrib in log))
            except Exception, e:
                print >>sys.stderr, traceback.format_exc()
                print >>sys.stderr, "whoopsie! some problem (%s) with ticket: %s" % (str(e), t)


def ticketdetail(ticket_num, *details):
    """Print all the detail about the ticket specified
    
    Optionally filter to the specified detail"""

    server = _get_xmlrpc()
    ticket = server.ticket.get(ticket_num)
    attrs = ticket[3]

    if not details:
        details = attrs.keys()

    for i in details:
        detail = attrs.get(i, None)
        if not None:
            print "#%s %s: %s" % (ticket_num, i, detail)

def ticketnew(to, summary, tickettype, component, description):
    """Make a new ticket

    to - the person to whom the ticket will be given
    summary - the ticket summary
    tickettype - what sort of ticket is it? (defect? task? enhancement?)
    component - the targetted component
    description - a longer description
    """
    class ValidationError(Exception):
        def __init__(self, field, fieldname, possibles):
            self.field = field
            self.fieldname = fieldname
            self.possibles = possibles

    server = _get_xmlrpc()
    try:
        tickettypes = server.ticket.type.getAll()
        if tickettype not in tickettypes:
            raise ValidationError(tickettype, "type", tickettypes)

        componenttypes = server.ticket.component.getAll()
        if component not in componenttypes:
            raise ValidationError(component, "component", componenttypes)

        ticket_number = server.ticket.create(summary, 
                                             description, 
                                             { "owner": to,
                                               "type": tickettype, 
                                               "component": component },
                                             True)
        print ticket_number
    except ValidationError, e:
        print >>sys.stderr, "ticketnew to summary type component description"
        print >>sys.stderr, "%s not valid %s, supported values: %s" % (e.field,
                                                                       e.fieldname,
                                                                       " ".join(e.possibles))
        sys.exit(1)

def ticketupdate(ticket_number, field, value):
    """Simple update for tickets

    field - the ticket field to update
    value - the value to change the ticket field to."""
    server = _get_xmlrpc()
    m = re.match("#([0-9]+)", ticket_number)
    if m:
        ticket_number = m.group(1)
        
    ticket = server.ticket.get(ticket_number)
    if field == "description":
        newticket = server.ticket.update(
            ticket_number,
            description
            )
    else:
        newticket = server.ticket.update(
            ticket_number,
            "changing %s" % field,
            { field: value }
            )

## More admin stuff

def help(*lst):
    print __doc__

if __name__ == "__main__":
    try:
        cmd = sys.argv[1]
        if cmd in ["help", "shell", "loginemacs", "methods", "method", 
                   "release", 
                   "ticket", "tickets", "ticketnew", "ticketdetail", "ticketupdate",
                   "wiki","wikiput","wikiedit"]:
            exec "%s(*%s)" % (cmd, sys.argv[2:])
    except Exception, e:
        print e
        #help()

# End

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
 * milestonenew
            - make a new milestone so that you can attach tickets to it.
 * milestonecomplete
            - mark a milestone as done.

Author: Nic Ferrier, nferrier@woome.com
"""

import re
import os
import sys
import xmlrpclib
import tempfile
from ConfigParser import ConfigParser
import traceback
from os.path import expanduser as expanduserpath
from os.path import exists as path_exists

def _get_ini_file(section, trac_instance=None):
    """Read in the trac_cmd ini file and return a dict of the specified section.

    If trac_instance is specified it acts as a qualifier... find the
    section with the specified .trac_instance specifier

    eg: "dev" might be used with this config:

     [Auth]
     trac_url = https://tracserver1
     username = user
     password = secret

     [Auth.dev]
     trac_url = https://tracserver2
     username = user
     password = plain

    The location of the ini file can be overridden with an environment
    variable TRAC_INI. 

    By default the ini file is found in ~
    """

    trac_ini_file = os.environ.get(
        "TRAC_INI", 
        expanduserpath("~/.trac_cmd.ini")
        )
    if not path_exists(trac_ini_file):
        return {}
    try:
        fd = open(trac_ini_file)
        cp = ConfigParser()
        cp.readfp(fd)
        return dict(cp.items(
                section if not trac_instance else "%s.%s" % (
                    section, 
                    trac_instance
                    )
                ))
    except Exception, e:
        print >>sys.stderr, "reading the trac_cmd ini file failed because: %s" % str(e)
        return {}


## Authentication and "login" stuff

def _login_auth(username, password, trac_url):
    token = re.sub("(http[s]*)://(.*)", "\\1://%s:%s@\\2" % (username, password), trac_url)
    os.environ["TRAC_URL"] = token
    return os.environ["TRAC_URL"]
    
def _login(username=None, password=None, trac_url=None, trac_instance=None):
    """Do login filling in gaps from ini file if necessary"""
    auth_details = {
        "username": username, 
        "password": password, 
        "trac_url": trac_url
        }
    if None in auth_details.values():
        cfg_details = _get_ini_file("Auth", trac_instance=trac_instance)
        auth_details.update(cfg_details)
    return _login_auth(**auth_details)


def loginemacs(username, password, trac_url=None):
    """Return the environment settings for doing trac env in emacs"""
    print """(setenv "TRAC_URL" \"%s\")""" % _login(username, password, trac_url)
    
def shell(username, trac_url=None, command=None):
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

def _get_trac_url(trac_instance=None):
    trac_url = os.environ.get("TRAC_URL", None)
    if not trac_url:
        return _login(trac_instance=trac_instance)
    return trac_url

def _get_xmlrpc(trac_instance=None):
    """Called by everything to actually do the login"""
    trac_url = _get_trac_url(trac_instance=trac_instance)
    xr = xmlrpclib.ServerProxy("%s/login/xmlrpc" % trac_url)
    return xr

## RPC exposure methods

def methods(*patterns, **kwargs):
    """Lists the xmlrpc methods available from trac."""
    trac_instance = kwargs.get("trac_instance", None)
    matched = True
    server = _get_xmlrpc(trac_instance=trac_instance)
    for methName in server.system.listMethods():
        if patterns:
            matched = False
            for pat in patterns:
                matched = re.match(pat, methName)
        if matched:
            print methName

def method(*methnames, **kwargs):
    """Shows the documentation for the xmlrpc methods specified.
    More than 1 method may be specified.
    """
    trac_instance = kwargs.get("trac_instance", None)
    server = _get_xmlrpc(trac_instance=trac_instance)
    for meth in methnames:
        print server.system.methodHelp(meth)

## Wiki handling methods

def wiki(page_name, version=None, trac_instance=None):
    """Simply retrieves the wiki page

    Prepends with an s-expression of page attributes."""

    server = _get_xmlrpc(trac_instance=trac_instance)
    print "(:tracwikiproperties ("
    for name,value in server.wiki.getPageInfo(page_name).iteritems():
        print ":%s \"%s\"" % (name,value)
    print "))"
    content = server.wiki.getPage(page_name)
    print content.encode("utf8")

def wikiput(page_name, content=None, trac_instance=None):
    """Puts the page back to the wiki

    content is the page or "-" to indicate that the content is on
    stdin."""

    server = _get_xmlrpc(trac_instance=trac_instance)
    if content == None or content == "-":
        content = sys.stdin.read()
    try:
        server.wiki.putPage(page_name, content, {})
    except:
        print >>sys.stderr, "page does not exist: %s" % page_name
        sys.exit(1)

def wikiedit(page_name, trac_instance=None):
    """Simple operating system trac integration.

    Opens the page and calls $EDITOR on it, then puts the resulting page
    back to the wiki once you quit the editor."""

    server = _get_xmlrpc(trac_instance=trac_instance)
    try:
        content = server.wiki.getPage(page_name)
    except:
        print >>sys.stderr, "page does not exist: %s" % page_name
        sys.exit(1)
    else:
        filedesc, file_name = tempfile.mkstemp()
        fd = os.fdopen(filedesc, "w+")
        try:
            print >>fd, content.encode("utf8")
        except IOError:
            print >>sys.stderr, "couldn't write to a temp file for editing %s" % page_name
            sys.exit(1)
        else:
            fd.close()
            os.spawnlp(
                os.P_WAIT, 
                os.environ["EDITOR"], 
                os.environ["EDITOR"], 
                file_name)
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

def tickets(*args, **kwargs): ##kwargs specifically support trac_instance
    """Alias for ticket(*args)"""
    ticket(*args, **kwargs)

def _milestone_tickets(ticks, server):
    """Return a list of tickets, dereferncing milestones if appropriate"""
    milestonere = re.compile("^milestone:(?P<milestone_name>[A-Za-z0-9_-]+)")
    hashticketre = re.compile("^#(?P<ticket>[0-9]+)")
    ticklist = []
    for t in ticks:
        m = milestonere.match(t)
        if m:
            milestone_ticks = server.ticket.query("milestone=%s" % m.group("milestone_name"))
            ticklist += milestone_ticks
        else:
            tm = hashticketre.match(t)
            if tm:
                t = tm.group("ticket")
            ticklist.append(t)
    return ticklist


def ticket(*ticks, **kwargs): ##kwargs specifically support trac_instance
    """Produce output about each ticket specified.

    Tickets can either be ticket numbers or \#ticketnumber or a
    milestone reference such as:

       milestone:tag

    when a milestone reference is used all the tickets attached to the
    milestone are referenced.

    milestone references and ticket numbers can be mixed, eg:

      \#6672 milestone:release_201011180943 1001
    """
    trac_instance = kwargs.get("trac_instance", None)
    def ticket_fmt(prefix, s):
        # Anti-charlie device
        # Sometimes he seems to add random unicode chars to strings
        # There is no rhyme or reason to this
        # We try and strip them out.
        if type(s) == type(u""):
            s=s.encode('ascii', 'replace')
        return re.sub("\n", "\n%s " % prefix, str(s))

    server = _get_xmlrpc(trac_instance=trac_instance)
    ticklist = _milestone_tickets(ticks, server)
    # Now loop round and get the details
    for t in ticklist:
        tick = server.ticket.get(t)
        attrs = tick[3]
        for name,value in attrs.iteritems():
            try:
                print "%d %s %s" % (int(t), name, ticket_fmt("%d %s" % (int(t), name), value))
            except:
                print >>sys.stderr, "whoops! encoding problem"
        changelog = server.ticket.changeLog(t)
        for log in changelog:
            try:
                print u"%d %s" % (int(t), u" ".join(ticket_fmt(int(t), attrib) for attrib in log))
            except Exception, e:
                print >>sys.stderr, traceback.format_exc()
                print >>sys.stderr, "whoopsie! some problem (%s) with ticket: %s" % (str(e), t)


def ticketdetail(ticket_num, *details, **kwargs):
    """Print all the detail about the ticket specified
    
    Optionally filter to the specified detail"""
    trac_instance = kwargs.get("trac_instance", None)
    server = _get_xmlrpc(trac_instance=trac_instance)
    ticket = server.ticket.get(ticket_num)
    attrs = ticket[3]

    if not details:
        details = attrs.keys()

    for i in details:
        detail = attrs.get(i, None)
        if not None:
            print ("#%s %s: %s" % (ticket_num, i, detail)).encode("ascii", "replace")

def ticketnew(to, summary, tickettype, component, description, trac_instance=None):
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

    server = _get_xmlrpc(trac_instance=trac_instance)
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
        print >>sys.stderr, "%s not valid %s, supported values: %s" % (
            e.field,
            e.fieldname,
            " ".join(e.possibles)
            )
        sys.exit(1)

# This controls whether the field must be forced or not
# A field can be forced by adding force: before it
# eg:
#   force:milestone
FIELD_REQUIRES_FORCE = ["milestone"]

def _force_guard(field, current_attribs):
    """Check if the field name is specified in FIELD_REQUIRES_FORCE.

    We also check that the current attribs have a value."""
    field_re = re.compile("(?P<force>force:)*(?P<fieldname>[A-Za-z0-9_-]+)")
    fieldm = field_re.match(field)
    fieldname = fieldm.group("fieldname")
    if fieldname in FIELD_REQUIRES_FORCE:
        if current_attribs.get(fieldname) and fieldm.group("force") != "force:":
            return False
    return fieldname

def ticketupdate(ticket, field, value, description="", trac_instance=None):
    """Simple update for tickets.

    'ticket'  should be a ticket or a milestone ref - milestone:rc_...
    'field'   the ticket field to update, use 'description' for general text
    'value'   the value to change the ticket field to.
    """

    server = _get_xmlrpc(trac_instance=trac_instance)
    tickets = _milestone_tickets([ticket], server)
    for t in tickets:
        if field == "description":
            newticket = server.ticket.update(
                int(ticket_number),
                value
                )
        else:
            current = server.ticket.get(t)
            fieldname = _force_guard(field, current[3])
            if not(fieldname):
                print >>sys.stderr, "you can't set %s=%s on %s without specifying force like force:milestone milestonename" % (
                    field, 
                    value,
                    t
                    )
                sys.exit(1)
            else:
                newticket = server.ticket.update(
                    int(t),
                    description if description != "" else "changing %s" % fieldname,
                    { fieldname: value.strip() }
                    )


from datetime import datetime

def milestones(trac_instance):
    """List the milestones"""
    server = _get_xmlrpc(trac_instance=trac_instance)
    for m in server.ticket.milestone.getAll():
        print m
    
def milestonenew(tag, trac_instance=None):
    """Make a new milestone.

    tag - the tag to give the milestone.
    """
    server = _get_xmlrpc(trac_instance=trac_instance)
    server.ticket.milestone.create(tag, {})
    print tag

def milestonecomplete(tag, trac_instance=None):
    """Mark the milestone completed.

    tag - the tag to give the milestone.
    """
    server = _get_xmlrpc(trac_instance=trac_instance)
    server.ticket.milestone.update(tag, {"completed":datetime.now()})

def milestoneupdate(tag, name, value, trac_instance=None):
    """Update the specified milestone"""
    server = _get_xmlrpc(trac_instance=trac_instance)
    server.ticket.milestone.update(tag, {name:value})
    print value
    

## More admin stuff

def help(*lst):
    print __doc__

def fnre(s, regex, grp=0):
    """Functional regex match"""
    m = re.match(regex, s)
    if m:
        return m.group(grp)
    return None

def ticket_number(str):
    m = re.match("#*([0-9]+)", str)
    ticket_number = m.group(1) if m else str
    return ticket_number

def ticket_or_milestone(str):
    m = re.match("(#*(?P<tn>[0-9]+))|(?P<mname>milestone:.*)", str)
    if m.group("tn"):
        return m.group("tn")
    if m.group("mname"):
        return m.group("mname")

    return str

    
from cmd import Cmd
class SysArgsCmd(Cmd):
    """Let's you use cmd with arg lists"""

    def onecmd(self, args):
        """Make a onecmd that operates on an array"""
        cmdarg = args[0]
        try:
            func = getattr(self, 'do_' + cmdarg)
        except AttributeError:
            return self.default(args[1:])
        else:
            return func(args[1:])

    def do_help(self, arg):
        """A version of help that deals with the array args"""
        return Cmd.do_help(self, " ".join(arg))


class TracCmd(SysArgsCmd):
    """Make a cmd parser for trac commands"""
    trac_instance = None

    def _set_common_opts(self, parser):
        """If we can get option parser working for the sub commands this could do the common stuff"""
        parser.add_option()

    def do_methods(self, arg):
        """Display help on a xmlrpc methods"""
        kwargs = { "trac_instance": self.trac_instance }
        methods(*arg, **kwargs)

    def do_method(self, arg):
        """Display help on a specific xmlrpc method"""
        kwargs = { "trac_instance": self.trac_instance}
        method(*arg, **kwargs)

    def do_xmlrpc(self, arg):
        """Execute some xmlrpc. No type conversion is done."""
        server = _get_xmlrpc(trac_instance=self.trac_instance)
        try:
            fn = getattr(server, arg[0])
        except AttributeError:
            print >>sys.stderr, "no such function"
        else:
            if len(arg) > 0:
                print fn(*arg[1:])
            else:
                print fn()

    def do_wiki(self, arg):
        """Get the wiki page specified"""
        kwargs = { "trac_instance": self.trac_instance }
        wiki(*arg, **kwargs)

    def do_wikiedit(self, arg):
        """Use your editor to edit the specified wiki page"""
        kwargs = { "trac_instance": self.trac_instance }
        wikiedit(*arg, **kwargs)

    def do_wikiput(self, arg):
        """Put a page back to the wiki"""
        kwargs = { "trac_instance": self.trac_instance }
        wikiput(*arg, **kwargs)

    def do_milestones(self, arg):
        """List all the milestones"""
        kwargs = { "trac_instance": self.trac_instance }
        milestones(*arg, **kwargs)

    def do_milestonenew(self, arg):
        """Make a new milestone"""
        kwargs = { "trac_instance": self.trac_instance }
        milestonenew(*arg, **kwargs)

    def do_milestonecomplete(self, arg):
        """Complete the milestone"""
        kwargs = { "trac_instance": self.trac_instance }
        milestonecomplete(*arg, **kwargs)

    def do_milestoneupdate(self, arg):
        """Update the milestone"""
        kwargs = { "trac_instance": self.trac_instance }
        milestoneupdate(*arg, **kwargs)

    def do_ticketdetail(self, arg):
        """Print specific details about a ticket"""
        kwargs = { "trac_instance": self.trac_instance }
        ticketdetail(ticket_number(arg[0]), *arg[1:], **kwargs)

    def do_td(self, arg):
        """Alias for ticketdetail"""
        kwargs = { "trac_instance": self.trac_instance }
        ticketdetail(ticket_number(arg[0]), *arg[1:], **kwargs)

    def do_tickets(self, arg):
        """Present information about each ticket specified.

Tickets can either be ticket numbers or #ticketnumber or a
milestone reference such as:

  milestone:tag

when a milestone reference is used all the tickets attached to the
milestone are referenced.

milestone references and ticket numbers can be mixed, eg:

  #6672 milestone:release_201011180943 1001

If you use #ticket in a shell be careful to escape the #
"""
        kwargs = { "trac_instance": self.trac_instance }
        ticket(*arg, **kwargs)

    def do_ticket(self, arg):
        """Alias for tickets"""
        self.do_tickets(arg)

    def do_ticketupdate(self, arg):
        """Update a ticket with a specified field.

        ticketupdate number field value [description]
        """
        tn = ticket_number(arg[0])
        kwargs = { "trac_instance": self.trac_instance }
        ticketupdate(tn, *arg[1:], **kwargs)

    def do_ticketnew(self, arg):
        """Make a new ticket

        to summary tickettype component description
        """

        # Todo
        # Suggestion: if no parameters are presented we could ask for the data with an edit form
        # (pop up a form into an editor and read back data specified)
        kwargs = { "trac_instance": self.trac_instance }
        ticketnew(*arg, **kwargs)


if __name__ == "__main__":
    from StringIO import StringIO
    cmdproc = TracCmd(StringIO())

    from optparse import OptionParser
    p = OptionParser()
    p.add_option(
        "-T",
        "--trac",
        dest="trac_instance",
        help="specify the name of the trac instance in your .trac_cmd.ini file",
        default=None,
        )
        
    o,a = p.parse_args(sys.argv[1:])
    cmdproc.trac_instance = o.trac_instance
    ret = cmdproc.onecmd(a)

# End

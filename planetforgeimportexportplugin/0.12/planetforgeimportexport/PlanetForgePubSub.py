# -*- coding: utf-8 -*-

from trac.core import *

from trac.util.html import html
from trac.util.text import print_table, printout
from trac.util.translation import _, N_, gettext

from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, Chrome

from trac.db.api import with_transaction

from trac.admin.api import IAdminCommandProvider, IAdminPanelProvider

from trac.loader import get_plugin_info

from trac.ticket import model
from trac.ticket.model import Ticket

from urlparse import urlparse
import json
import urllib
import urllib2

debug=False


#peer to notify
peer='http://hub.coclico.bearstech.com/'
#peer='http://127.0.0.1:8001/'

#use htaccess ?
use_htaccess = False

#htacess credential
htaccess = {
    'login' : '',
    'pwd' : '',
}

#Functions to call
functions = { #'status' : 'status/index.php',
              #'owner' : 'owner/index.php',
              'create' : 'pubsubhub/ticket/create',
              }

def notify(field, args) :
    #args['token'] = token
    if debug :
        log = open('/tmp/ticket_listener', 'a')
        log.writelines('in \n')
    if not functions.has_key(field) :
        return
    url = peer + functions[field]
    postData=json.dumps(args)
    if use_htaccess :
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, htaccess['login'], htaccess['pwd'])
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
    else :
        opener = urllib2.build_opener()
    req =  urllib2.Request(url, postData, {'Content-Type': 'application/json'})
    urllib2.install_opener(opener)
    res = urllib2.urlopen(req)
    if debug :
        log.writelines('url : %s\nPOST data : %s\nresponse : %s\ninfo : %s'%(url, str(args), res.read(), res.info()))
        log.writelines('out \n')
        log.close()

class PlanetForgePubSub(Component):
    implements(IAdminCommandProvider, IAdminPanelProvider, ITemplateProvider, ITicketChangeListener)


    # CLI part (trac-admin /path/to/trac planetforge pubsub out hub.planetforge.com:4559

    def get_admin_commands(self):
        yield ('planetforge pubsub', '', 'Planetforge in/out pubsubs via pubsub', None, self.cli_pubsub)

    def cli_pubsub(self) :
        print "Not implemented yet."


    # WEB part (/admin/planetforge/pubsub)

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    def get_htdocs_dirs(self):
        return []

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('planetforge', 'PlanetForge', 'pubsub', 'PubSub')

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TRAC_ADMIN')
        return './pubsub.html', {}


    def _getRepr(self, ticket) :
        return {'authtoken':self.env.base_url + ticket.values['reporter'] + str(ticket.id),
                'status': ticket.values['status'],
                'description': ticket.values['description'],
                'id': ticket.id,
                'reporter': ticket.values['reporter'],
                'cc': ticket.values['cc'],
                'component': ticket.values['component'],
                'summary': ticket.values['summary'],
                'priority': ticket.values['priority'],
                'owner': ticket.values['owner'],
                'version': ticket.values['version'] if ticket.values.has_key('version') else 0,
                'milestone': ticket.values['milestone'] if ticket.values.has_key('milestone') else '',
                'keywords': ticket.values['keywords'],
                'type': ticket.values['type']}


    def ticket_created(self, ticket):
        res = self._getRepr(ticket)
        notify('create', res)
        """Called when a ticket is created."""
        return

        
    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        
        if old_values.has_key('status') :
            data = {'id' : ticket.id,
                    'base_url' : self.env.base_url,
                    'old_status' : old_values['status'],
                    'new_status' : ticket.values['status'],
                    'comment' : comment.encode('utf-8'),
                    }
            notify('status', data)

        elif old_values.has_key('owner') :
            data = {'id' : ticket.id,
                    'base_url' : self.env.base_url,
                    'old_owner' : old_values['owner'],
                    'new_owner' : ticket.values['owner'],
                    'comment' : comment.encode('utf-8'),
                    }
            notify('owner', data)
        return
        
	
    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        return

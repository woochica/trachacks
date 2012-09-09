# -*- coding: utf-8 -*-
import re
from time import time
from trac.core import *
from trac.web import IRequestHandler, ITemplateStreamFilter
from trac.util.datefmt import format_date, format_time
from trac.util import Markup
from trac.ticket import Ticket
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href
from util import validate_acl
import ezPyCrypto

class GringottsPage(Component):
    implements(INavigationContributor, ITemplateStreamFilter, ITemplateProvider, IRequestHandler)

    def __init__(self):
        pass

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if re.search('/gringotts', req.path_info):
            return 'gringotts'
        else:
            return ''

    def get_navigation_items(self, req):
        url = req.href.gringotts()
        if req.perm.has_permission("REPORT_VIEW"):
            yield 'mainnav', 'gringotts', \
                  Markup('<a href="%s">%s</a>' % \
                         (url , "Gringotts"))

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('gringotts', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        # Add Stylesheet here, so that the ticket page gets it too :)
        add_stylesheet(req, 'gringotts/gringotts.css')
        return stream

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/gringotts(?:/([a-zA-Z0-9]+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['gringlet'] = match.group(1)
            return 1

    def process_request(self, req):
        gringlet = req.args.get('gringlet')

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Do we want an edit page?
        if gringlet:
            cursor.execute('SELECT MAX(version) FROM gringotts WHERE name=%s', (gringlet,))
            try:
                version = int(cursor.fetchone()[0])
            except:
                version = 0

            messages = []
            action = 'edit'
            if req.method == 'POST' and req.args.has_key('save'):
                if int(req.args['version']) != version:
                    # Collision
                    messages.append('Someone else has editted this Gringlet and your changes have been lost!')
                else:

                    if not validate_acl(req, req.args['acl']):
                        messages.append('Your change to the ACL would have locked you out.')
                        messages.append('Please change it accordingly and try again.')
                        
                        data = {
                          'action': 'edit',
                          'edit_rows': '20',
                          'messages': messages,
                          'gringlet': {
                            'name': gringlet,
                            'version': version,
                            'source': req.args['text'],
                            'acl': req.args['acl']
                          }
                        }

                        add_stylesheet(req, 'common/css/wiki.css')
                        return 'gringlet.html', data, None

                    # Save the update
                    key = str(self.config.get('gringotts', 'key'))
                    k = ezPyCrypto.key(key)
                    text = k.encStringToAscii(str(req.args['text']))
                    cursor.execute('INSERT INTO gringotts (name, version, time, text, acl) '
                                   'VALUES (%s, %s, %s, %s, %s)',
                                   (gringlet, (version+1), int(time()), text,
                                    req.args['acl']))
                    db.commit()
                    version += 1
                    
                    messages.append('Gringlet saved successfully.')
                    action = 'view'


            if version > 0:
                cursor.execute('SELECT text, acl FROM gringotts WHERE name=%s AND version=%s',
                               (gringlet,version))
                source,acl = cursor.fetchone()
                key = str(self.config.get('gringotts', 'key'))
                k = ezPyCrypto.key(key)
                source = k.decStringFromAscii(source)
            else:
                source = 'Enter the text for your Gringlet here'
                if req.authname == 'anonymous':
                    acl = ''
                else:
                    acl = req.authname

            # If we are allowed, then show the edit page, otherwise just show the listing
            if validate_acl(req, acl):
                if not req.args.has_key('action') or req.args['action'] != 'edit':
                  action = 'view'
                data = {
                  'action': action,
                  'edit_rows': '20',
                  'messages': messages,
                  'gringlet': {
                    'name': gringlet,
                    'version': version,
                    'source': source,
                    'acl': acl
                  }
                }
            else:
                messages.append("You do not have the necessary permission to see this Gringlett")
                data = {
                  'action': 'view',
                  'messages': messages
                }

            add_stylesheet(req, 'common/css/wiki.css')
            return 'gringlet.html', data, None

        # Listing page
        cursor.execute('SELECT name,acl FROM gringotts g1 WHERE version='
                       '(SELECT MAX(version) FROM gringotts g2 WHERE g1.name=g2.name) '
                       'ORDER BY name')

        names = []
        for name,acl in cursor:
            names.append({'name': name,
                          'permitted': validate_acl(req, acl)})

        data = {
          'gringlets' : {
            'list': names
          }
        }
        return 'gringotts.html', data, None



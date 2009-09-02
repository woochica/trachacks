# -*- coding: utf-8 -*-
import re
from time import time
from trac.log import logger_factory
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
            req.hdf['wiki.edit_rows'] = 20

            cursor.execute('SELECT MAX(version) FROM gringotts WHERE name=%s', (gringlet,))
            try:
                version = int(cursor.fetchone()[0])
            except:
                version = 0

            if req.method == 'POST' and req.args.has_key('save'):
                if int(req.args['version']) != version:
                    # Collision
                    req.hdf['messages'] = [ 'Someone else has editted this Gringlet and your changes have been lost!' ]
                else:

                    if not validate_acl(req, req.args['acl']):
                        messages = []
                        messages.append('Your change to the ACL would have locked you out.')
                        messages.append('Please change it accordingly and try again.')
                        
                        req.hdf['messages'] = messages
                        req.hdf['gringlet.version'] = version
                        req.hdf['gringlet.source'] = req.args['text']
                        req.hdf['gringlet.acl'] = req.args['acl']
                        
                        add_stylesheet(req, 'common/css/wiki.css')
                        return 'gringlet.cs', None

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
                    
                    req.hdf['messages'] = [ 'Gringlet saved successfully.' ]


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
            
                req.hdf['gringlet.version'] = version
                req.hdf['gringlet.source'] = source
                req.hdf['gringlet.acl'] = acl

                add_stylesheet(req, 'common/css/wiki.css')
                return 'gringlet.cs', None

        # Listing page
        cursor.execute('SELECT name,acl FROM gringotts g1 WHERE version='
                       '(SELECT MAX(version) FROM gringotts g2 WHERE g1.name=g2.name) '
                       'ORDER BY name')

        names = []
        for name,acl in cursor:
            names.append({'name': name,
                          'permitted': validate_acl(req, acl)})

        req.hdf['gringlets.list'] = names
        req.hdf['gringotts_href'] = req.href.gringotts()
        
        return 'gringotts.cs', None



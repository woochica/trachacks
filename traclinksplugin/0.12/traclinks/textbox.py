#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.filters.transform import Transformer
from pkg_resources import ResourceManager
from trac.attachment import Attachment
from trac.core import Component, implements, ExtensionPoint
from trac.resource import Resource
from trac.util.datefmt import format_datetime
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.api import IWikiSyntaxProvider
from trac.util.text import quote_query_string

class TextBox(Component):
    """ Generate TracLinks in search box for:
    { wiki: report: query: ticket: attachment: source: diff: log: milestone: timeline: search: }
    """
    implements (ITemplateStreamFilter, ITemplateProvider)
    
    def list_namespaces(self):
        providers = ExtensionPoint(IWikiSyntaxProvider).extensions(self.compmgr)
        for provider in providers:
            for (namespace, formatter) in provider.get_link_resolvers():
                self.log.debug('namespace: %s' % namespace)
    
    #ITemplateProvider methods
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        return [('traclinks', ResourceManager().resource_filename(__name__, 'htdocs'))]
    
    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
#        self.list_namespaces()
        # generate TracLink string
        resource = None
        if filename in ['ticket.html', 'wiki_view.html', 'report_view.html', 'milestone_view.html', 'agilo_ticket_view.html'] \
                and 'context' in data:
            resource = data['context'].resource
        elif filename in ['search.html']: # search:
            resource = Resource('search', data['query'])
        elif filename in ['browser.html']: # source:
            resource = data['context'].resource
            if resource.parent and resource.parent.realm == 'repository':
                resource.id = '%s/%s' % (resource.parent.id, resource.id)
                resource.parent = None
        elif filename in ['revisionlog.html']: # log:
            resource = data['context'].resource
            resource.realm = 'log'
            if resource.parent and resource.parent.realm == 'repository':
                resource.id = '%s/%s' % (resource.parent.id, resource.id)
                resource.parent = None
            revranges = data.get('revranges',None)
            rev = data.get('rev',None)
            if revranges: resource.version = '%s:%s' % (revranges.a, revranges.b)
            elif rev: resource.version = rev 
        elif filename in ['attachment.html']:
            if isinstance(data['attachment'], Attachment): # attachment:
                resource = data['attachment'].resource
            else:
                pass # attachment list page of the ticket; no TracLinks defined
        elif filename in ['timeline.html']: # timeline:
            resource = Resource('timeline', format_datetime(data['precisedate'], 'iso8601'))
        elif filename in ['changeset.html']:
            if data['changeset']: # changeset:
                resource = data['context'].resource
                if resource.parent and resource.parent.realm == 'repository':
                    resource.id = '%s/%s' % (resource.id, resource.parent.id) # OK, I know
                    resource.parent = None
                if data['restricted']: resource.id = '%s/%s' % (resource.id, data['new_path'])
            else: # diff:
                args = req.args
                old_path, new_path = args.get('old_path', ''), args.get('new_path','')
                old_rev, new_rev = args.get('old'), args.get('new')
                if old_path == new_path: # diff:path@1:3 style
                    resource = Resource('diff', old_path, '%s:%s' % (old_rev, new_rev))
                else: # diff:path@1//path@3 style
                    if old_rev: old_path += '@%s' % old_rev
                    if new_rev: new_path += '@%s' % new_rev
                    resource = Resource('diff', '%s//%s' % (old_path, new_path))
        elif filename in ['query.html']:
            if 'report_resource' in data:
                resource = data['report_resource']
            else:
                resource = Resource('query', data['query'].to_string().replace("\n", "")[7:])
        else:
            pass
        # link hash
        if filename in ['browser.html', 'ticket.html', 'agilo_ticket_view.html']:
            add_script(req, 'traclinks/js/jquery.ba-hashchange.js')
            add_script(req, 'traclinks/js/onhashchange.js')
        #
        if resource:
            traclinks = '%s' % (resource.id)
            if resource.version != None:
                traclinks += (resource.realm == 'ticket' and '?version=%s' or '@%s') % resource.version
            if resource.parent and resource.parent.id:
                traclinks += ':%s:%s' % (resource.parent.realm, resource.parent.id)
                if resource.parent.version != None:
                    traclinks += '@%s' % resource.parent.version
            if ' ' in traclinks: traclinks = '"%s"' % traclinks # surround quote if needed
            traclinks = '%s:%s' % (resource.realm, traclinks)
            # new ticket template
            if resource.id == None and resource.realm == 'ticket':
                v = data['ticket'].values
                keyvalue = ['%s=%s' % (k, quote_query_string(v[k])) for k in v.keys() if v[k] not in (None, '')]
                traclinks = '[/newticket?%s]' % '&'.join(keyvalue)
            return stream | Transformer('//input[@id="proj-search"]').attr('value', traclinks).attr('size', '50')
        return stream

# Implemented and tested:
"""
 - wiki:WikiStart
 - ticket:1
 - ticket:1?version=1    # NOTE: ticket:1@1 is not work
 - report:1 (SQL)
 - report:7 (Query)
 - query:owner=admin
 - attachment:test.txt:ticket:1
 - attachment:image.png:wiki:WikiStart # linked but not searchable
 - attachment:"file name with spaces.txt:wiki:日本語 と 空白"
 - log:@1:2
 - log:/trunk@1
 - log:anotherrepo/trunk@1
 - diff:@1:2
 - diff:trunk@1:2
 - diff:trunk//tags
 - diff:trunk@1//tags@2
 - diff:anotherrepo/trunk@2//anotherrepo/tags@3
 - milestone:milestone1
 - timeline:2012-02-22
 - search:searchtext
 - source:/trunk/file.txt
 - source:/trunk/file.txt@2
 - source:anotherrepo/trunk/file.txt
 - source:anotherrepo/trunk/file.txt@3
 - comment:1:ticket:1
 - source:/trunk/file.txt#L20
"""

# Not Implemented Yet

# Won't Implement
# 'raw-attachment', 
# 'htdocs'
# diff:...#file0
# /ticket/2?action=diff&version=1
# /ticket/2?action=comment-diff&cnum=2&version=1

# Known bugs
# /ticket/2?version=1 makes 'ticket:2@1' but it's wrong
 

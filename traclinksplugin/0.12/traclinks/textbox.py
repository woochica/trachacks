#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.filters.transform import Transformer
from trac.attachment import Attachment
from trac.core import Component, implements
from trac.resource import Resource
from trac.util.datefmt import format_datetime
from trac.web.api import ITemplateStreamFilter

class TextBox(Component):
    """ Generate TracLinks in search box for:
    { wiki: report: query: ticket: attachment: source: diff: log: milestone: timeline: search: }
    """
    implements (ITemplateStreamFilter)
    
    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
#       providers = ExtensionPoint(IWikiSyntaxProvider).extensions(self.compmgr)
        resource = None
        if filename in ['ticket.html', 'wiki_view.html', 'report_view.html', 'milestone_view.html'] \
                and 'context' in data:
            resource = data['context'].resource
        elif filename in ['search.html']: # search:
            resource = Resource('search', data['query'])
        elif filename in ['browser.html']: # source:
            resource = data['context'].resource
            if resource.parent and resource.parent.realm == 'repository':
                resource.id = '/'.join((resource.parent.id, resource.id))
                resource.parent = None
        elif filename in ['revisionlog.html']: # log:
            resource = data['context'].resource
            resource.realm = 'log'
            if resource.parent and resource.parent.realm == 'repository':
                resource.id = '/'.join((resource.parent.id, resource.id))
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
            resource = Resource('timeline', format_datetime(data['fromdate'], 'iso8601'))
        elif filename in ['changeset.html']:
            if data['changeset']: # changeset:
                resource = data['context'].resource
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
        if resource:
            traclinks = '%s:%s' % (resource.realm, resource.id)
            if resource.version != None:
                traclinks += '@%s' % resource.version
            if resource.parent and resource.parent.id:
                resource = resource.parent
                traclinks += ':%s:%s' % (resource.realm, resource.id)
                if resource.version != None:
                    traclinks += '@%s' % resource.version
            return stream | Transformer('//input[@id="proj-search"]').attr('value', traclinks).attr('size', '50')
        return stream

# Implemented and tested:
"""
 - wiki:WikiStart
 - ticket:1
 - report:1 (SQL)
 - report:7 (Query)
 - query:owner=admin
 - attachment:test.txt:ticket:1
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
"""

# Won't Implement
# 'comment', 
# 'raw-attachment', 
# 'htdocs'

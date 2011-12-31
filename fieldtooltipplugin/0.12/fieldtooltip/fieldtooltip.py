#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi import XML
from genshi.core import QName
from genshi.filters.transform import START, END
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.wiki.api import IWikiChangeListener, WikiSystem
from trac.wiki.formatter import wiki_to_html

class FieldTooltip(Component):
    """ Provides tooltip for ticket fields. (In Japanese/KANJI) チケットフィールドのツールチップを提供します。
        if wiki page named 'help/'''field-name'''' is supplied, use it for tooltip text. """
    implements(ITemplateStreamFilter, IWikiChangeListener)
    _titleMode = False
    _default_pages = {  'reporter': 'The author of the ticket.',
                        'type': 'The nature of the ticket (for example, defect or enhancement request). See TicketTypes for more details.',
                        'component': 'The project module or subsystem this ticket concerns.',
                        'version': 'Version of the project that this ticket pertains to.',
                        'keywords': 'Keywords that a ticket is marked with. Useful for searching and report generation.',
                        'priority': 'The importance of this issue, ranging from trivial to blocker. A pull-down if different priorities where defined.',
                        'milestone': 'When this issue should be resolved at the latest. A pull-down menu containing a list of milestones.',
                        'assigned to': 'Principal person responsible for handling the issue.',
                        'owner': 'Principal person responsible for handling the issue.',
                        'cc': 'A comma-separated list of other users or E-Mail addresses to notify. Note that this does not imply responsiblity or any other policy.',
                        'resolution': 'Reason for why a ticket was closed. One of fixed, invalid, wontfix, duplicate, worksforme.',
                        'status': 'What is the current status? One of new, assigned, closed, reopened.',
                        'summary': 'A brief description summarizing the problem or issue. Simple text without WikiFormatting.',
                        'description': 'The body of the ticket. A good description should be specific, descriptive and to the point. Accepts WikiFormatting.'}
    _wiki_prefix = 'help/'

    def __init__(self):
        self._pages = {} # for each trac Project
        # retrieve initial wiki contents for field help
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        wiki_pages = WikiSystem(self.env).get_pages(FieldTooltip._wiki_prefix)
        for page in wiki_pages:
            cursor.execute("SELECT text FROM wiki WHERE name = '%s' ORDER BY version DESC LIMIT 1" % page)
            for (text,) in cursor:
                self._pages[page[len(FieldTooltip._wiki_prefix):]] = text

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html': 
            return stream | FieldTooltipFilter(self, req)
        return stream

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        self._pages[page.name[len(FieldTooltip._wiki_prefix):]] = page.text
        
    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self._pages[page.name[len(FieldTooltip._wiki_prefix):]] = page.text
        
    def wiki_page_deleted(self, page):
        if page.name[len(FieldTooltip._wiki_prefix):] in self._pages:
            del self._pages[page.name[len(FieldTooltip._wiki_prefix):]]
    
    def wiki_page_version_deleted(self, page):
        self._pages[page.name[len(FieldTooltip._wiki_prefix):]] = page.text
        
    def wiki_page_renamed(self, page, old_name):
        if old_name[len(FieldTooltip._wiki_prefix):] in self._pages:
            del self._pages[old_name[len(FieldTooltip._wiki_prefix):]]
        self._pages[page.name[len(FieldTooltip._wiki_prefix):]] = page.text


class FieldTooltipFilter(object):
    """ stream の <label for="field-ZZZZZ"> および <th id="h_ZZZZZ"> に対して、
        title="ZZZZZ | zzzzzz" という属性で説明を追加し、
        rel="#tooltip-ZZZZZ" という属性を追加し、
        <div id="tooltip-ZZZZZ"> zzzzz </div> という要素を追加します。
        div要素の中身はWikiフォーマットされたHTMLで説明を追加します。太字やリンクなども表現されます。
        
               通常のHTMLでは title属性がポップアップしますが、
        jquery cluetip plugin では、{local:true} と指定することで、relで指定したIDのdivをポップアップできます。
        jquery tooltip plugin では bodyHandler で 当該divを返すようにすることで、そのdivがポップアップします。
                ターゲットの next要素をポップアップするプラグインもあったような気がする。全部実現できるよ。
        """
     
    def __init__(self, parent, req):
        self.parent = parent
        self.req = req
    
    def __call__(self, stream):
        after_stream = {}
        depth = 0
        for kind, data, pos in stream:
            if kind is START:
                attr_value = None
                depth += 1
                data = self._add_title(data, 'label', 'for', 'field-', after_stream, depth)
                data = self._add_title(data, 'th', 'id', 'h_', after_stream, depth)
                yield kind, data, pos
            elif kind is END:
                yield kind, data, pos
                if str(depth) in after_stream:
                    for subevent in after_stream[str(depth)]:
                        yield subevent
                    del after_stream[str(depth)]
                depth -= 1
            else:
                yield kind, data, pos

    def _add_title(self, data, tagname, attr_name, prefix, after_stream, depth):
        """ after_stream has side effect """
        tag, attrs = data
        if tag.localname == tagname:
            attr_value = attrs.get(attr_name)
            if attr_value and attr_value.startswith(prefix):
                attr_value = attr_value[len(prefix):]
                if attr_value in self.parent._pages:
                    text = self.parent._pages.get(attr_value)
                    attrs |= [(QName('title'), attr_value + ' | ' + text)]
                    attrs |= [(QName('rel'), '#tooltip-' + attr_value)]
                    text = attr_value + ":\n" + wiki_to_html(text, self.parent.env, self.req)
                    after_stream[str(depth)] = \
                        XML('<div id="%s" class="tooltip" style="display: none">%s</div>' \
                            % ('tooltip-' + attr_value, text))
                    data = tag, attrs
                elif attr_value in FieldTooltip._default_pages:
                    text = FieldTooltip._default_pages.get(attr_value)
                    attrs |= [(QName('title'), attr_value + ' | ' + text)]
                    attrs |= [(QName('rel'), '#tooltip-' + attr_value)]
                    text = attr_value + ":\n" + wiki_to_html(text, self.parent.env, self.req)
                    after_stream[str(depth)] = \
                        XML('<div id="%s" class="tooltip" style="display: none">%s</div>' \
                            % ('tooltip-' + attr_value, text))
                    data = tag, attrs
        return data

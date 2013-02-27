#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.core import QName
from genshi.filters.transform import START, END
from pkg_resources import ResourceManager
from trac.cache import cached
from trac.core import Component, implements
from trac.mimeview import Context
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.wiki.api import IWikiChangeListener, WikiSystem
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage


class FieldTooltip(Component):
    """ Provides tooltip for ticket fields. (In Japanese/KANJI) チケットフィールドのツールチップを提供します。
        if wiki page named 'help/field-name is supplied, use it for tooltip text. """
    implements(ITemplateStreamFilter, ITemplateProvider, IWikiChangeListener)
    _default_pages = {'reporter': 'The author of the ticket.',
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
                      'description': 'The body of the ticket. A good description should be specific, descriptive and to the point. Accepts WikiFormatting.',
                      # workflow
                      'leave': 'makes no change to the ticket.',
                      'resolve': '-',
                      'reassign': '-',
                      'accept': '-',
                      'reopen': '-',
                      }
    # for locale=ja
    _default_pages.update({
                      'reporter.ja': u'このチケットの作成者',
                      'type.ja': u'このチケットの種類 (例えば、不具合 (defect), 機能追加 (enhancement request) など) 詳細は [trac:TicketTypes TicketTypes] 参照。',
                      'component.ja': u'このチケットが紐づくモジュールやサブシステム。',
                      'version.ja': u'このチケットが関連するプロジェクトのバージョン。',
                      'keywords.ja': u'チケットに付与するキーワード。検索や、レポートの生成で利用できる。',
                      'priority.ja': u'\'\'trivial\'\' から \'\'blocker\'\' の範囲で示されるチケットの重要度。定義した他の優先度を含めプルダウンで表示。',
                      'milestone.ja': u'このチケットを遅くともいつまでに解決すべきか。マイルストーン一覧をプルダウンで表示。',
                      'assigned to.ja': u'次にチケットを扱うべき人。',
                      'owner.ja': u'チケットを扱っている人。',
                      'cc.ja': u'通知すべきユーザ名またはE-Mailアドレスのカンマ区切りリスト。なお、責任などのどんな意味も持っていない。',
                      'resolution.ja': u'チケットが解決された際の理由。{{{修正した(fixed)}}}、{{{無効なチケット(invalid)}}}、{{{修正しない(wontfix)}}}、{{{他のチケットと重複(duplicate)}}}、{{{再現しない(worksforme)}}}など。',
                      'status.ja': u'チケットの現在の状態。 {{{new}}}, {{{assigned}}}, {{{closed}}}, {{{reopened}}} など。',
                      'summary.ja': u'問題や課題の簡単な説明。WikiFormatting されない。',
                      'description.ja': u'チケットの内容。WikiFormatting される。状況を特定する、的を射た説明がよい。',
                      # workflow
                      'leave.ja': u'変更しない。',
                      'resolve.ja': u'解決したものとする。',
                      'reassign.ja': u'割り当てを変える。',
                      'accept.ja': u'引き受ける。',
                      'reopen.ja': u'再び扱う。',
                      })
    # blocking, blockedby for MasterTicketsPlugin, TicketRelationsPlugin
    # position for QueuesPlugin
    # estimatedhours for EstimationToolsPlugin, TracHoursPlugin, SchedulingToolsPlugin
    # startdate, duedate for SchedulingToolsPlugin
    # totalhours for TracHoursPlugin
    # duetime for TracMileMixViewPlugin
    # completed,storypoints,userstory for TracStoryPointsPlugin
    # fields = "'estimatedhours', 'hours', 'billable', 'totalhours', 'internal'" for T&E;
    #    See http://trac-hacks.org/wiki/TimeEstimationUserManual
    # and any more default tooltip text...

    _wiki_prefix = 'help/'

    def __init__(self):
        pass

    @cached
    def pages(self, db):
        # retrieve wiki contents for field help
        pages = {}
        prefix_len = len(FieldTooltip._wiki_prefix)
        wiki_pages = WikiSystem(self.env).get_pages(FieldTooltip._wiki_prefix)
        for page in wiki_pages:
            pages[page[prefix_len:]] = WikiPage(self.env, page, db=db).text
        return pages

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('fieldtooltip', ResourceManager().resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            # jquery tools tooltip ... tested
            add_script(req, 'fieldtooltip/jquerytools/jquery.tools.min.js')
            add_script(req, 'fieldtooltip/jquerytools/enabler.js')
            add_stylesheet(req, 'fieldtooltip/jquerytools/jquery_tools_tooltip.css')
            # jquery tooltip ... dont work collectly
#            add_script(req, 'fieldtooltip/jquerytooltip/jquery.dimensions.js')
#            add_script(req, 'fieldtooltip/jquerytooltip/jquery.tooltip.js')
#            add_script(req, 'fieldtooltip/jquerytooltip/enabler.js')
            # jquery powertip ... tested
#            add_script(req, 'fieldtooltip/jquerypowertip/jquery.powertip.js')
#            add_script(req, 'fieldtooltip/jquerypowertip/enabler.js')
#            add_stylesheet(req, 'fieldtooltip/jquerypowertip/jquery.powertip.css')
            # cluetip ... tested
#            add_script(req, 'fieldtooltip/cluetip/jquery.hoverIntent.js')
#            add_script(req, 'fieldtooltip/cluetip/jquery.cluetip.js')
#            add_script(req, 'fieldtooltip/cluetip/enabler.js')
#            add_stylesheet(req, 'fieldtooltip/cluetip/jquery.cluetip.css')

            return stream | FieldTooltipFilter(self, req)
        return stream

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        del self.pages

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        del self.pages

    def wiki_page_deleted(self, page):
        del self.pages

    def wiki_page_version_deleted(self, page):
        del self.pages

    def wiki_page_renamed(self, page, old_name):
        del self.pages


class FieldTooltipFilter(object):
    """ Add description in 'title' attribute as title="ZZZZZ | zzzzzz",
        add 'rel' attribute as rel="#tooltip-ZZZZZ", 
        add element as <div id="tooltip-ZZZZZ"> zzzzz </div>,
        for <label for="field-ZZZZZ"> and <th id="h_ZZZZZ"> element in a stream.
        The content in the div will be HTML-formatted, we can use bold, italic, link or so.

        It occurs
        pop up the title attribute by default,
        pop up a div element pointed in rel, with jquery cluetip plugin and {local:true} style,
        pop up a div element returned by bodyHandler, with jquery tooltip plugin,
        pop up the next element (=div added by this plugin), with jquery tools tooltip.

        (In Janapese/KANJI)
        stream の <label for="field-ZZZZZ"> および <th id="h_ZZZZZ"> に対して、
        title="ZZZZZ | zzzzzz" という属性で説明を追加し、
        rel="#tooltip-ZZZZZ" という属性を追加し、
        <div id="tooltip-ZZZZZ"> zzzzz </div> という要素を追加します。
        div要素の中身はWikiフォーマットされたHTMLで説明を追加します。太字やリンクなども表現されます。

               通常のHTMLでは title属性がポップアップします。
        jquery cluetip plugin を使う場合、{local:true} と指定することで、relで指定したIDのdivがポップアップします。
        jquery tooltip plugin を使う場合、bodyHandler で 当該divを返すようにすることで、そのdivがポップアップします。
        jquery tools tooltip を使う場合、removeAttr('title') することで next要素(=div)がポップアップします。
        """

    def __init__(self, parent, req):
        self.parent = parent
        self.context = Context.from_request(req)
        self.locale = self.context.req.locale

    def __call__(self, stream):
        after_stream = {}
        depth = 0
        for kind, data, pos in stream:
            if kind is START:
                depth += 1
                # add title and rel attribute to the element
                data = self._add_title(data, 'label', 'for', 'action_', after_stream, depth)
                data = self._add_title(data, 'label', 'for', 'field-', after_stream, depth)
                data = self._add_title(data, 'th', 'id', 'h_', after_stream, depth)
                yield kind, data, pos
            elif kind is END:
                yield kind, data, pos
                # add div element after the element
                if str(depth) in after_stream:
                    for subevent in after_stream[str(depth)]:
                        yield subevent
                    del after_stream[str(depth)]
                depth -= 1
            else:
                yield kind, data, pos

    def _add_title(self, data, tagname, attr_name, prefix, after_stream, depth):
        """ In case of
            data parameter as element has same tagname attribute for the parameter and
            attribute named the attr_name starts with the prefix,
            add description in title attribute and rel attribute to the element
            and store div element generated to after_stream[depth] for later use.

            (In Japanese/KANJI)
            data で与えられた要素が、引数で指定された tagname であり、attr_name 属性の値が prefix で始まる場合、
                        説明文をtitle属性およびrel属性としてその要素に設定します。
                        またそのとき、after_stream[depth] に DIV 要素を格納します。
        """
        element, attrs = data
        attr_value = attrs.get(attr_name)
        if element.localname == tagname and attr_value and attr_value.startswith(prefix):
            attr_value = attr_value[len(prefix):]
            attr_value_locale = "%s.%s" % (attr_value, self.locale)
            text = self.parent.pages.get(attr_value_locale,
                   self.parent.pages.get(attr_value,
                   FieldTooltip._default_pages.get(attr_value_locale,
                   FieldTooltip._default_pages.get(attr_value))))
            if text:
                attrs |= [(QName('title'), attr_value + ' | ' + text)]
                attrs |= [(QName('rel'), '#tooltip-' + attr_value)]
                img = tag.img(src='%s/chrome/common/wiki.png' \
                              % self.context.req.base_url,
                              alt='?', align='right')
                a = tag.a(img, href='%s/wiki/%s%s' \
                           % (self.context.req.base_url, FieldTooltip._wiki_prefix, attr_value))
                after_stream[str(depth)] = \
                tag.div(a, '%s:\n' % attr_value,
                        format_to_html(self.parent.env, self.context, text, False),
                        id='tooltip-' + attr_value,
                        class_='tooltip',
                        style='display: none')
                data = element, attrs
        return data

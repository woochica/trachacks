# codereview.py

import re
import time, datetime

from trac.core import Component, implements, Interface, ExtensionPoint
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from trac.timeline import ITimelineEventProvider
from trac.versioncontrol.diff import get_diff_options, hdf_diff
from trac import util
from trac.util import Markup
from trac.util.datefmt import format_datetime, pretty_timedelta, to_timestamp
from trac.util.text import pretty_size
from trac.wiki import IWikiSyntaxProvider, wiki_to_html, wiki_to_oneliner
from trac.wiki.api import IWikiMacroProvider
from trac.attachment import Attachment, ILegacyAttachmentPolicyDelegate, AttachmentModule

from codereview.util import pretty_err 
from codereview.model import CodeReviewPool, CodeReview, status_str, str_status

def attachment_to_hdf(env, req, db, attachment):
    """
    This function have been removed from 0.11, this is copied from 0.10, then modified to 
    work with 0.11
    """
    if not db:
        db = env.get_db_cnx()
    hdf = {
        'filename': attachment.filename,
        'description': wiki_to_oneliner(attachment.description, env, db, req=req),
        'author': attachment.author,
        'ipnr': attachment.ipnr,
        'size': pretty_size(attachment.size),
        'time': format_datetime(attachment.date),
        'age': pretty_timedelta(attachment.date),
        'href': AttachmentModule(env).get_resource_url(attachment.resource, req.href)
    }
    return hdf

class ICodeReviewListener(Interface):

    def review_changed(env, cr_id, text, version, author, status, priority, req=None, ctime=None):
        """Called whenever a codereview page is changed."""


langs = {
         'c'   : ('c', '// %s'),
         'cpp' : ('cpp', '// %s'),
         'h'   : ('c', '// %s'),
         'py'  : ('python', '# %s'),
         'pyw' : ('python', '# %s'),
         'pl'  : ('perl', '# %s'),
         'rb'  : ('ruby', '# %s'),
         'php' : ('php', '// %s'),
         'php4': ('php', '// %s'),
         'php5': ('php', '// %s'),
         'asp' : ('asp', "' %s"),
         'aspx': ('asp', "' %s"),
         'sql' : ('sql', '-- %s'),
         'xml' : ('xml', '<!-- %s -->'),
         'html': ('xml', '<!-- %s -->'),
         'sh'  : ('sh', '# %s'),
        }


class CodeReviewSystem(Component):
    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    def get_wiki_syntax(self):
        yield (r"(?:\b|!)c\d+", lambda x, y, z: self._format_link(x, "code review", y[1:], y, z))

    def get_link_resolvers(self):
        return [('code review', self._format_link)]

    def _format_link(self, formatter, ns, target, label, fullmatch=None):
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT message FROM revision WHERE rev = %s" % target)
        row = cursor.fetchone()
        if row:
            title = row[0]
        else:
            title = None
        cursor.execute("SELECT COUNT(*) FROM codereview WHERE id = %s" % target)
        row = cursor.fetchone()
        if row:
            count = row[0]
        else:
            count = None
        if count:
            return Markup("<a href=\"%s\" title=\"%s\">%s</a>" % (self.env.href.CodeReview(target), title, label))
        else:
            return Markup("<a class=\"missing\" href=\"%s\" title=\"%s\">%s?</a>" % (self.env.href.CodeReview(target), title, label))

    def get_macros(self):
        yield "CodeSegment"

    def get_macro_description(self, name):
        return "The macro is used to display given file content."

    def render_macro(self, req, name, content):
        path, start_line, end_line, rev = [arg.strip() for arg in content.split(',')][:4]
        start_line = int(start_line)
        end_line = int(end_line)
        repos = self.env.get_repository()
        node = repos.get_node(path, rev)
        text = node.get_content().read()
        text = re.split(r'\n|\r\n?', text)
        text = '\n'.join(text[(start_line - 1):(end_line - 1)])
        ext = path.split('.')[-1].lower()
        comment = "%s@%s line %s - line %s by CodeSegment Macro" % (path, rev, start_line, end_line)
        if ext in langs:
            comment = langs[ext][1] % comment
            text = "{{{\n#!%s\n%s\n\n%s\n}}}" % (langs[ext][0], comment, text)
        else:
            text = "{{{\n%s\n\n%s\n}}}" % (comment, text)
        html = wiki_to_html(text, self.env, None)
        return html


class CodeReviewMain(Component):
    implements(IRequestHandler,
               INavigationContributor,
               ITemplateProvider,
               IPermissionRequestor,
               ITimelineEventProvider)


    def get_permission_actions(self):
        return ['CODE_REVIEW_ADMIN',]

    def get_active_navigation_item(self, req):
        return 'CodeReview'

    def get_navigation_items(self, req):
        if (not req.perm.has_permission('CODE_REVIEW_VIEW')) and \
           (not req.perm.has_permission('CODE_REVIEW_EDIT')) and \
           (not req.perm.has_permission('CODE_REVIEW_ADMIN')):
            return
        yield ('mainnav', 'CodeReview',
               Markup('<a href="%s">CodeReview</a>' %
                      self.env.href.CodeReview()))


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('cr', resource_filename(__name__, 'htdocs'))]

    def match_request(self, req):
        return req.path_info.lower() == '/codereview'



    def get_timeline_filters(self, req):
        if req.perm.has_permission('CODE_REVIEW_VIEW') or \
           req.perm.has_permission('CODE_REVIEW_EDIT') or \
           req.perm.has_permission('CODE_REVIEW_ADMIN'):
            yield ('codereview', 'Code review changes')


    def get_timeline_events(self, req, start, stop, filters):
        if 'codereview' in filters:
            crp = CodeReviewPool(self.env)
            for t, author, text, cr_id, status, version, message in \
                crp.get_codereviews_by_time(to_timestamp(start), to_timestamp(stop)):
                if status == str_status["NoNeedToReview"]:
                    continue
                elif status == str_status["CompletelyReview"]:
                    title = Markup('CodeReview : [ <em title="%s" >%s</em> ] completed by %s' %
                                   (message, cr_id, author))
                elif version == 1:
                    title = Markup('CodeReview : [ <em title="%s" >%s</em> ] created by %s' %
                                  (message, cr_id, author))
                else:
                    title = Markup('CodeReview : [ <em title="%s" >%s</em> ] edited by %s' %
                                  (message, cr_id, author))
                href = "%s/%s" % (self.env.href.CodeReview(), cr_id)
                text = wiki_to_oneliner(text, self.env, self.env.get_db_cnx(), shorten=True, req=req)
                yield 'codereview', href, title, t, author, text

    def _render_nav(self, req):
        req.hdf['main.href'] = self.env.href.CodeReview()
        req.hdf['completed.href'] = self.env.href.CodeReview(completed='on')
        req.hdf['manager.href'] = self.env.href.CodeReviewManager()
        req.hdf['main'] = 'yes'
        req.hdf['completed'] = 'no'
        req.hdf['manager'] = 'no'

    def _display_html(self, req):
        base_href = self.env.href.base
        crp = CodeReviewPool(self.env)

        db = self.env.get_db_cnx()

        is_completed = req.args.get('completed', '')

        keywords = {}

        action = req.args.get('action', '').strip()

        if req.args.get('comment', '').strip():
            keywords['comment'] = req.args.get('comment', '').strip().lower()

        req_author = req.args.get('author', '').strip().lower()
        if req_author:
            if ',' in req_author:
                keywords['author'] = [i.strip() for i in req_author.split(',') if i.strip()] 
            else:
                keywords['author'] = [req_author,]

        start_rev = int(self.env.config.get('codereview', 'start_rev', '0'))
        not_shown = self._get_not_shown()

        req.hdf['base_href'] = base_href
        req.hdf['search_href'] = self.env.href.CodeReview()

        if req.args.get('action', '') == 'search' and req.args.get('date', '').strip():
            re_date = re.compile('^(\d{4})(\d{2})(\d{2})$')
            req_date = re_date.match(req.args.get('date', '').strip())
            if req_date:
                try:
                    req_date = [int(v) for v in req_date.groups()]
                    keywords['start_date'] = time.mktime(datetime.date(*req_date).timetuple())
                    keywords['end_date'] = time.mktime((datetime.date(*req_date) + datetime.timedelta(1)).timetuple())
                except ValueError, error_info:
                    return pretty_err(req, 'Search keyword error', error_info)
            else:
                return pretty_err(req, 'Search keyword error', 'search date format should be yyyymmdd.')
        else:
            req_date = None

        if req.args.get('action', '') == 'search':
            if req.args.has_key('author'):
                req.hdf['search_author'] = req.args.get('author').strip()
            if req.args.has_key('comment'):
                req.hdf['search_comment'] = req.args.get('comment').strip()
            if req_date:
                req.hdf['search_date'] = req.args.get('date').strip()

        if is_completed:
            completed_items = crp.get_codereviews_by_key("Completed", start_rev, keywords, not_shown)
            for item in completed_items:
                item['url_cs'] = '%s/changeset/%s' % (base_href, item['rev'])
                item['url_cr'] = '%s/CodeReview/%s' % (base_href, item['rev'])
                item['msg'] = self._format_msg(item['msg'], db, req)
                item['reviewers'] = ', '.join(item['reviewers'])
                item['ctime'] = time.strftime("%b %d %H:%M", time.localtime(item['ctime']))

            req.hdf['completed.items'] = completed_items
            req.hdf['completed.len']   = len(completed_items)

            req.hdf['title'] = 'CodeReview Completed'
            req.hdf['main'] = 'no'
            req.hdf['completed'] = 'yes'

            return 'codereview.cs', None

        undergoing_items = crp.get_codereviews_by_key("Undergoing", start_rev, key=keywords, not_shown=not_shown)
        awaiting_items = crp.get_codereviews_by_key("Awaiting", start_rev, key=keywords, not_shown=not_shown)

        for item in awaiting_items:
            item['url_cs'] = "%s/changeset/%s" % (base_href, item['rev'])
            item['url_cr'] = "%s/CodeReview/%s" % (base_href, item['rev'])
            item['msg'] = self._format_msg(item['msg'], db, req)
            item['ctime'] = time.strftime("%b %d %H:%M", time.localtime(item['ctime']))

        for item in undergoing_items:
            item['url_cs'] = '%s/changeset/%s' % (base_href, item['rev'])
            item['url_cr'] = '%s/CodeReview/%s' % (base_href, item['rev'])
            item['msg'] = self._format_msg(item['msg'], db, req)
            item['reviewers'] = ', '.join(item['reviewers'])
            item['ctime'] = time.strftime("%b %d %H:%M", time.localtime(item['ctime']))

        req.hdf['missing.items'] = awaiting_items
        req.hdf['missing.len']   = len(awaiting_items)

        req.hdf['incompleted.items'] = undergoing_items
        req.hdf['incompleted.len']   = len(undergoing_items)
        req.hdf['title'] = 'CodeReviewMain'
        req.hdf['nntr_href'] = self.env.href.CodeReview()
        return 'codereview.cs', None

    def _format_msg(self, msg, db, req):
        try:
            return wiki_to_oneliner(msg, self.env, db, req=req)
        except Exception, e:
            self.env.log.error("ERROR in _format_msg(%s):%s" % (msg, e))
            return msg

    def _get_not_shown(self):
        prefixs = self.env.config.get('codereview', 'prefix', '')
        prefixs = [prefix.strip().lower() for prefix in prefixs.split(',') if prefix.strip()]

        msgs = self.env.config.get('codereview', 'msg', '')
        msgs = [msg.strip().lower() for msg in msgs.split(',') if msg.strip()]
        return {'prefix':prefixs, 'msg':msgs}


    def _get_search_keywords(self, req):
        ret = {}
        for k in ('author', 'comment', 'date'):
            if req.args.get(k, '').strip():
                ret[k] = req.args.get(k).strip()
        if ret:
            ret['action'] = 'search'
        return ret


    def _render_nntr(self, req):
        crp = CodeReviewPool(self.env)
        last_rev = crp.get_rev_count()
        revs = range(last_rev+1)
        author = util.get_reporter_id(req)
        for k in req.args.keys():
            try:
                cr_id = int(k)
            except:
                continue
            if req.args.get(k).lower() == 'on' and cr_id in revs:
                CodeReview(self.env, cr_id, author).set_no_need_to_review()
        req.redirect(self.env.href.CodeReview(**self._get_search_keywords(req)))


    def _render_critical(self, req):
        crp = CodeReviewPool(self.env)
        last_rev = crp.get_rev_count()
        revs = range(last_rev+1)
        author = util.get_reporter_id(req)
        for k in req.args.keys():
            try:
                cr_id = int(k)
            except:
                continue
            if req.args.get(k).lower() == 'on' and cr_id in revs:
                CodeReview(self.env, cr_id, author).set_to_critical()
        req.redirect(self.env.href.CodeReview(**self._get_search_keywords(req)))



    def process_request(self, req):
        if req.perm.has_permission('CODE_REVIEW_ADMIN') or \
                   req.perm.has_permission('CODE_REVIEW_EDIT'):
            pass
        else:
            req.perm.assert_permission('CODE_REVIEW_VIEW')
        if req.args.has_key('action'):
            if req.args.get('action') == 'No need to review':
                self._render_nntr(req)
            if req.args.get('action') == 'Set to critical':
                self._render_critical(req)

        self._render_nav(req)
        return self._display_html(req)
        



class CodeReviewPage(Component):
    implements(IRequestHandler,
               INavigationContributor,
               ITemplateProvider,
               IPermissionRequestor,
               ILegacyAttachmentPolicyDelegate)
    change_listeners = ExtensionPoint(ICodeReviewListener)

    def get_permission_actions(self):
        return ['CODE_REVIEW_EDIT',]

    def check_attachment_permission(self, action, username, resource, perm):
        """ Respond to the various actions into the legacy attachment
        permissions used by the Attachment module. """
        self.env.log.error("realm = %s" % resource.parent.realm)
        if resource.parent.realm == 'CodeReview':
            if action == 'ATTACHMENT_VIEW':
                return 'CODE_REVIEW_VIEW' in perm(resource.parent)
            if action in ['ATTACHMENT_CREATE', 'ATTACHMENT_DELETE']:
                if 'CODE_REVIEW_EDIT' in perm(resource.parent):
                    return True
                elif 'CODE_REVIEW_ADMIN' in perm(resource.parent):
                    return True
                else:
                    return False

    def get_active_navigation_item(self, req):
        return 'CodeReview'

    def get_navigation_items(self, req):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('cr', resource_filename(__name__, 'htdocs'))]

    def match_request(self, req):
        re_obj = re.compile(r'^/codereview/([0-9]+).*$', re.I).match(req.path_info)
        if re_obj:
            req.args['id'] = re_obj.groups()[0]
            return True
        else:
            return False

    def _render_nav(self, req):
        req.hdf['main.href'] = self.env.href.CodeReview()
        req.hdf['completed.href'] = self.env.href.CodeReview(completed='on')
        req.hdf['manager.href'] = self.env.href.CodeReviewManager()
        req.hdf['main'] = 'yes'
        req.hdf['completed'] = 'no'
        req.hdf['manager'] = 'no'

    def process_request(self, req):
        if req.perm.has_permission('CODE_REVIEW_ADMIN') or \
                    req.perm.has_permission('CODE_REVIEW_EDIT'):
            pass
        else:
            req.perm.assert_permission('CODE_REVIEW_VIEW')
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'common/css/code.css')
        self._render_nav(req)
        if req.args.has_key('action'):
            if req.args.get('action') == 'edit':
                return self._display_edit(req)
            elif req.args.get('action') == 'preview':
                return self._display_edit(req)
            elif req.args.get('action') == 'save':
                return self._save_cr(req)
            elif req.args.get('action') == 'delete':
                return self._delete_cr(req)
            elif req.args.get('action') == 'history':
                return self._history_cr(req)
            elif req.args.get('action') == 'diff':
                return self._diff_cr(req)
        return self._display_html(req)
    
    def _diff_cr(self, req):
        add_stylesheet(req, 'common/css/diff.css')
        cs_id = req.args.get('id')
        old_version = req.args.get('old_version', 1)
        version = req.args.get('version', 1)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            version_author, version_status, newtext = self._get_version_record(cursor, cs_id, version)
            oldversion_author, oldversion_status, oldtext = self._get_version_record(cursor, cs_id, old_version)
        except ValueError:
            return pretty_err(req, 'Version Error')
        ctime = round(time.time(), 2)
        diff_style, diff_options = get_diff_options(req)
        context = 3
        for option in diff_options:
            if option.startswith('-U'):
                context = int(option[2:])
                break
        if context < 0:
            context = None
        changes = hdf_diff(oldtext.splitlines(), newtext.splitlines(), context=context,
                           ignore_blank_lines='-B' in diff_options,
                           ignore_case='-i' in diff_options,
                           ignore_space_changes='-b' in diff_options)
        req.hdf['version.diff'] = changes

        req.hdf['version_author'] = version_author
        req.hdf['oldversion_author'] = oldversion_author
        req.hdf['version_status'] = status_str[version_status]
        req.hdf['oldversion_status'] = status_str[oldversion_status]
        req.hdf['ctime'] = time.ctime(ctime)
        req.hdf['old_version'] = old_version
        req.hdf['version'] = version
        req.hdf['rev'] = cs_id
        req.hdf['update.href'] = self.env.href.CodeReview(cs_id, action='diff')
        return 'codereviewdiff.cs', None

    def _get_version_record(self, cursor, cs_id, version):
        cursor.execute("SELECT author, status, text FROM codereview " \
                       "WHERE id=%s AND version=%s", (int(cs_id), version))
        record = cursor.fetchone()
        try:
            author, status, text = record[:3]
            if text is None:
                text = ''
            return author, status, text
        except:
            raise ValueError
    def _history_cr(self, req):
        cs_id = req.args.get('id')
        cr = CodeReview(self.env, int(cs_id))
        if not cr.is_existent_rev():
            return pretty_err(req, 'Review ID error', 'No ChangeSet %s, it cannot ' \
                                'CodeReview for a Non-existent ChangeSet' % cs_id)
        history_items = []
        for item in cr.get_all_items():
            item['time'] = time.ctime(item['time'])
            item['status'] = status_str[item['status']]
            item['cr_href'] = '%s/%s?version=%s' % (self.env.href.CodeReview(), cs_id, item['version'])
            history_items.append(item)
        if history_items:
            req.hdf['history.edit_href'] = '%s/%s?action=edit' % (self.env.href.CodeReview(), cs_id)
        else:
            req.hdf['history.edit_href'] = '%s/%s?action=new' % (self.env.href.CodeReview(), cs_id)
        req.hdf['history.count'] = len(history_items)
        req.hdf['history.items'] = history_items
        req.hdf['history.cr_id'] = cs_id
        req.hdf['history.href'] = '%s/%s' % (self.env.href.CodeReview(), cs_id)
        return 'codereviewhistory.cs', None



    def _render_attachment(self, req, cr_id, perm = False):
        for idx, attachment in enumerate(Attachment.select(self.env, 'CodeReview',
                                                           cr_id)):
            hdf = attachment_to_hdf(self.env, db=self.env.get_db_cnx(), req=req, attachment=attachment)
            req.hdf['codereview.attachments.%s' % idx] = hdf
        if req.perm.has_permission('CODE_REVIEW_EDIT') and perm:
            req.hdf['codereview.attach_href'] = self.env.href.attachment('CodeReview',
                                                                     cr_id)

    def _display_html(self, req):
        cs_id = int(req.args.get('id'))
        cr = CodeReview(self.env, int(cs_id))
        if req.args.get('version'):
            try:
                req_ver = int(req.args.get('version'))
            except:
                req_ver = 0
        else:
            req_ver = 0
        if req.args.has_key('delete_info'):
            req.hdf['delete_info'] = req.args.get('delete_info')
        if not cr.is_existent_rev():
            return pretty_err(req, 'Review ID error', 'No ChangeSet %s, it cannot ' \
                                'CodeReview for a Non-existent ChangeSet' % cs_id)
        if req_ver:
            if cr.is_existent_ver(req_ver):
                ver = req_ver
            else:
                ver = 0
        else:
            ver = cr.get_current_ver()
        if not ver:
            req.hdf['page_class'] = "None"
            if req_ver:
                req.hdf['title'] = "CodeReview r%s version: %s is non-existent" \
                                   % (cs_id, req_ver)
                req.hdf['message'] = "CodeReview r%s version: %s is non-existent" \
                                   % (cs_id, req_ver)
                req.hdf['create_href'] = "%s/%s" % (self.env.href.CodeReview(), \
                                                cs_id)
            else:
                req.hdf['title'] = "CodeReview r%s is non-existent" % cs_id
                req.hdf['message'] = "CodeReview r%s is non-existent, Do you want to create it?" % cs_id
                req.hdf['create_href'] = "%s/%s" % (self.env.href.CodeReview(), \
                                                cs_id)
            return 'codereviewpage.cs', None
        else:
            req.hdf['page_class'] = "View"
            req.hdf['title'] = "CodeReview r%s" % cs_id
            item = cr.get_item()
            self._render_attachment(req, cs_id)
            if cr.get_current_ver() == ver:
                req.hdf['delete_href'] = "%s/%s" % (self.env.href.CodeReview(), cs_id)
            else:
                req.hdf['source_text'] = item['text'] or ''
            req.hdf['status'] = status_str[item['status']]
            req.hdf['authors'] = ', '.join(item['reviewers'])
            req.hdf['text'] = item['text'] and wiki_to_html(item['text'], self.env, req) or ''
            req.hdf['time'] = time.ctime(item['time'])
            req.hdf['cr_id'] = cs_id
            req.hdf['version'] = ver
            req.hdf['priority'] = item['priority']
            req.hdf['cs_href'] = "%s/changeset/%s" % (self.env.href.base, cs_id)
            req.hdf['edit_href'] = "%s/CodeReview/%s" % (self.env.href.base, cs_id)
            return 'codereviewpage.cs', None



    def _display_edit(self, req):
        req.perm.assert_permission('CODE_REVIEW_EDIT')
        cs_id = req.args.get('id')
        cr = CodeReview(self.env, int(cs_id))
        if not cr.is_existent_rev():
            return pretty_err(req, 'Review ID error', 'No ChangeSet %s, it cannot ' \
                                'CodeReview for a Non-existent ChangeSet' % cs_id)
        item = cr.get_item()
        if cr.is_existent():
            item['reviewers'] = ', '.join(item['reviewers'])
            #ver, ctime, status, text, priority = record
            ver = item['version']
            status = item['status']
            priority = item['priority']
            ctime = time.ctime(item['time'])
            text = item['text'] or ''
        else:
            authors = ''
            ver = 0
            status = str_status["UndergoingReview"]
            text = ''
            ctime = ''
            priority = 'normal'
        sourcelists = [{'i':i, 'v': '[[CodeSegment(%s, 1, 2, %s)]]'%(v, cs_id)} \
                                    for i, v in enumerate(cr.get_all_pathes())]
        if len(sourcelists) > 0:
            req.hdf['source_count'] = len(sourcelists)
            req.hdf['sourcelists'] = sourcelists
        if req.args.get('action') == 'preview' and req.args.has_key('text'):
            req.hdf['preview'] = wiki_to_html(req.args.get('text'), self.env, req)
            req.hdf['text'] = req.args.get('text')
        else:
            req.hdf['text'] = text
        author = util.get_reporter_id(req)
        if req.args.has_key('req_version'):
            if ver != int(req.args.get('req_version')):
                if req.args.has_key('oldtext'):
                    req.hdf['oldtext'] = req.args.get('oldtext')
                else:
                    req.hdf['oldtext'] = req.args.get('text')
                req.hdf['version'] = req.args.get('req_version')
            else:
                req.hdf['version'] = ver
        else:
            req.hdf['version'] = ver
        self._render_attachment(req, cs_id, True)
        req.hdf['page_class'] = 'edit'
        req.hdf['time'] = ctime
        req.hdf['status'] = status
        req.hdf['reviewers'] = item['reviewers']
        req.hdf['author'] = author
        req.hdf['id'] = cs_id
        req.hdf['priority'] = priority
        req.hdf['cs_href'] = '%s/changeset/%s' % (self.env.href.base, cs_id)
        req.hdf['save_href'] = '%s/CodeReview/%s' % (self.env.href.base, cs_id)
        req.hdf['title'] = "Edit CodeReview r%s" % cs_id

        return 'codereviewpage.cs', None

    def _delete_cr(self, req):
        req.perm.assert_permission('CODE_REVIEW_EDIT')
        cs_id = int(req.args.get('id'))
        cr = CodeReview(self.env, int(cs_id))
        current_ver = cr.get_current_ver()
        if current_ver:
            cr.delete()
            req.args['delete_info'] = 'Codereview r%s version: %s has been deleted successfully.' % \
                                        (cs_id, current_ver)
            return self._display_html(req)
        else:
            return pretty_err(req, 'Cannot delete codereview r%s version: %s' % (cs_id, current_ver))


    def _save_cr(self, req):
        req.perm.assert_permission('CODE_REVIEW_EDIT')

        cs_id = req.args.get('id')
        req_ver = req.args.get('req_version')

        cr = CodeReview(self.env, int(cs_id))

        if not cr.is_existent_rev():
            return pretty_err(req, 'Review ID error', 'No ChangeSet %s, it cannot ' \
                                'CodeReview for a Non-existent ChangeSet' % cs_id)
        error_info = []

        try:
            req_ver = int(req_ver)
        except:
            error_info.append('No req_version, cannot know your version for editing.')
        
        if req.args.get('author').strip() == '':
            error_info.append('Author cannot be empty.')
        if req.args.get('text').strip() == '':
            error_info.append('CodeReview Content cannot be empty.')
        if req.args.get('status') not in [str(k) for k in status_str.keys()]:
            error_info.append('Status value is vaild.')
        if error_info:
            return pretty_err(req, 'Cannot save codereview', '<br>'.join(error_info))
        
        item = cr.get_item()
        if cr.is_existent():
            #item['text'] = item['text'] or ''
            if req_ver != item['version']:
                req.args['oldtext'] = req.args.get("text", " ")
                return self._display_edit(req)
            ver = int(item['version']) + 1
        else:
            if req_ver != 0:
                req.args['oldtext'] = req.args.get("text", " ")
                return self._display_edit(req)
            ver = 1
        
        if req.args.get('priority', '') in ('normal', 'critical'):
            item['priority'] = req.args.get('priority')
        
        item['text'] = req.args.get('text')
        item['time'] = round(time.mktime(time.localtime()), 2)
        item['author'] = req.args.get('author')
        item['status'] = int(req.args.get('status'))
        cr.set_item(item)
        cr.save()

        for change_listener in self.change_listeners:
            change_listener.review_changed(self.env,
                                           int(cs_id),
                                           req.args.get('text'),
                                           ver,
                                           req.args.get('author'),
                                           int(req.args.get('status')),
                                           item['priority'],
                                           req
                                          )
        req.redirect('%s/CodeReview/%s' % (self.env.href.base, cs_id))


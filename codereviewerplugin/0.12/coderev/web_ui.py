import re
import json
from trac.core import *
from trac.config import ListOption, Option
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler
from trac.ticket.model import Ticket

from genshi.builder import tag
from trac.resource import Resource
from trac.versioncontrol import RepositoryManager
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_html
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from tracopt.ticket.commit_updater import CommitTicketUpdater

from model import CodeReview

# default status choices - configurable but must always be exactly three
STATUSES = ['REJECTED','PENDING','PASSED']


class CodeReviewerModule(Component):
    """Base component for reviewing changesets."""
    
    implements(IRequestHandler, ITemplateProvider, IRequestFilter)
    
    # config options
    status_choices = ListOption('codereviewer', 'status_choices',
        default=STATUSES, doc="Review status choices.")
    status_default = Option('codereviewer', 'status_default',
        default='PENDING', doc="Default review status choice.")
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('coderev', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if self._valid_request(req):
            if req.method == 'POST':
                repo,changeset = get_repo_changeset(req)
                review = CodeReview(self.env, repo, changeset, req=req)
                if review.save(reviewer=req.authname, **req.args):
                    tickets = self._add_ticket_comment(req, review)
                    url = req.href(req.path_info,{'ticket':tickets})
                    req.send_header('Cache-Control', 'no-cache')
                    req.redirect(url+'#reviewbutton')
            add_stylesheet(req, 'coderev/coderev.css')
            add_script(req, 'coderev/coderev.js')
            add_script(req, '/coderev/coderev.html')
        elif req.path_info.startswith('/ticket/'):
            add_stylesheet(req, 'coderev/coderev.css')
        return template, data, content_type
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/coderev/')
    
    def process_request(self, req):
        repo,changeset = get_repo_changeset(req, check_referer=True)
        review = CodeReview(self.env, repo, changeset, self.status_default, req)
        data = {'review': review,
                'tickets': get_tickets(req),
                'status_choices': self.status_choices,
                'form_token': self._get_form_token(req)}
        req.send_header('Cache-Control', 'no-cache')
        return 'coderev.html', data, 'text/javascript' 
    
    # private methods
    def _valid_request(self, req):
        """Checks for changeset page and permissions."""
        if req.perm.has_permission('CHANGESET_VIEW'):
            return bool(get_repo_changeset(req)[0]) # found changeset in url?
        return False
    
    def _get_form_token(self, req):
        """Ajax POST requests require a __FORM_TOKEN param from the cookie."""
        # first search for req attribute
        if hasattr(req,'form_token') and req.form_token:
            return req.form_token
        
        # next look for token in the cookie
        if hasattr(req, 'environ'):
            cookie = req.environ.get('HTTP_COOKIE','')
            token_re = re.compile(r"trac_form_token=(?P<token>[a-z0-9]*)")
            match = token_re.search(cookie)
            if match:
                return match.groupdict()['token']
        return ''
    
    def _add_ticket_comment(self, req, review):
        summary = review.summaries[-1]
        
        # build comment
        if summary['status']:
            comment = "Code review set to %(status)s" % summary
        else:
            comment = "Code review comment"
        summary['_ref'] = review.changeset
        if review.repo:
            summary['_ref'] += '/' + review.repo
        comment += " for [%(_ref)s]:\n\n%(summary)s" % summary 
        
        # find and comment in tickets
        # TODO: handle when there's no explicitly named repo
        repo = RepositoryManager(self.env).get_repository(review.repo)
        changeset = repo.get_changeset(review.changeset)
        ticket_re = CommitTicketUpdater.ticket_re
        tickets = ticket_re.findall(changeset.message)
        
        # skip adding a ticket comment if there's no review summary
        if summary['summary']:
            for ticket in tickets:
                t = Ticket(self.env, ticket)
                t.save_changes(author=summary['reviewer'], comment=comment)
        return tickets


class CommitTicketReferenceMacro(WikiMacroBase):
    """This is intended to replace the builtin macro by providing additional
    code review status info for the changeset.  To use, disable the builtin
    macro as follows:
    
    [components]
    tracopt.ticket.commit_updater.committicketreferencemacro = disabled
    """
    
    status_choices = ListOption('codereviewer', 'status_choices',
        default=STATUSES, doc="Review status choices.")
    status_default = Option('codereviewer', 'status_default',
        default='PENDING', doc="Default review status choice.")
    
    def expand_macro(self, formatter, name, content, args={}):
        reponame = args.get('repository') or ''
        rev = args.get('revision')
        repos = RepositoryManager(self.env).get_repository(reponame)
        try:
            changeset = repos.get_changeset(rev)
            message = changeset.message
            
            # add review status to commit message (
            review = CodeReview(self.env, reponame, rev, self.status_default)
            class_ = STATUSES[self.status_choices.index(review.status)]
            message += '\n\n{{{#!html \n'
            message += '<div class="codereviewstatus">'
            message += '  <div class="system-message %s">' % class_.lower()
            message += '    <p>Code review status: '
            message += '      <span>%s</span>' % review.status
            message += '    </p>'
            message += '  </div>'
            message += '</div>'
            message += '\n}}}'
            
            rev = changeset.rev
            resource = repos.resource
        except Exception, e:
            message = content
            resource = Resource('repository', reponame)
        if formatter.context.resource.realm == 'ticket':
            ticket_re = CommitTicketUpdater.ticket_re
            if not any(int(tkt_id) == int(formatter.context.resource.id)
                       for tkt_id in ticket_re.findall(message)):
                return tag.p("(The changeset message doesn't reference this "
                             "ticket)", class_='hint')
        if ChangesetModule(self.env).wiki_format_messages:
            return tag.div(format_to_html(self.env,
                formatter.context('changeset', rev, parent=resource),
                message, escape_newlines=True), class_='message')
        else:
            return tag.pre(message, class_='message')


# common functions
def get_repo_changeset(req, check_referer=False):
    """Returns the changeset and repo as a tuple."""
    path=req.environ.get('HTTP_REFERER','') if check_referer else req.path_info
    pattern = r"/changeset/(?P<rev>[a-f0-9]+)(/(?P<repo>[^/?#]+))?"
    match = re.compile(pattern).search(path)
    if match:
        return (match.groupdict()['repo'],match.groupdict().get('rev',''))
    return None,None

def get_tickets(req):
    """Returns the changeset and repo as a tuple."""
    ticket_re = re.compile(r"ticket=(?P<id>[0-9]+)")
    path = req.environ.get('HTTP_REFERER','')
    return ticket_re.findall(path)

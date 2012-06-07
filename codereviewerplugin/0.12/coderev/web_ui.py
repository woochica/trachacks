import re
import json
import time
from subprocess import Popen, STDOUT, PIPE

from trac.core import *
from trac.config import ListOption, Option
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler
from trac.ticket.model import Ticket

from genshi.builder import tag
from trac.resource import Resource
from trac.versioncontrol import IRepositoryChangeListener, RepositoryManager
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_html
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from tracopt.ticket.commit_updater import CommitTicketUpdater

from model import CodeReview


class CodeReviewerModule(Component):
    """Base component for reviewing changesets."""
    
    implements(IRequestHandler, ITemplateProvider, IRequestFilter)
    
    # config options
    statuses = ListOption('codereviewer', 'status_choices',
        default=CodeReview.STATUSES, doc="Review status choices.")
    passed = ListOption('codereviewer', 'passed',
        default=[], doc="Ticket field changes on a PASSED submit.")
    failed = ListOption('codereviewer', 'failed',
        default=[], doc="Ticket field changes on a FAILED submit.")
    completeness = ListOption('codereviewer', 'completeness',
        default=[], doc="Ticket field values that enable ticket completeness.")
    command = Option('codereviewer', 'command',
        default='', doc="Command to execute upon ticket completeness.")
    
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
                review = CodeReview(self.env, repo, changeset, req)
                if review.save(reviewer=req.authname, **req.args):
                    tickets = self._update_tickets(req, review)
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
        review = CodeReview(self.env, repo, changeset, req)
        data = {'review': review,
                'tickets': get_tickets(req),
                'statuses': self.statuses,
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
    
    def _update_tickets(self, req, review):
        """Updates the tickets referenced by the given review's changeset
        with a comment of field changes.  Field changes and command execution
        may occur if specified in trac.ini and the review's changeset is the
        last one of the ticket."""
        status = review.encode(review.status).lower()
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
        
        # find and update tickets
        # TODO: handle when there's no explicitly named repo
        repo = RepositoryManager(self.env).get_repository(review.repo)
        changeset = repo.get_changeset(review.changeset)
        ticket_re = CommitTicketUpdater.ticket_re
        tickets = ticket_re.findall(changeset.message)
        
        invoked = False
        for ticket in tickets:
            tkt = Ticket(self.env, ticket)
            
            # determine ticket changes
            changes = {}
            if self._is_complete(ticket, tkt, review, failed_ok=True):
                changes = self._get_ticket_changes(tkt, status)
            
            # update ticket if there's a review summary or ticket changes
            if summary['summary'] or changes:
                for field,value in changes.items():
                    tkt[field] = value
                tkt.save_changes(author=summary['reviewer'], comment=comment)
            
            # check to invoke command
            if not invoked and self._is_complete(ticket, tkt, review):
                self._execute_command(status)
                invoked = True
        
        return tickets
    
    def _is_complete(self, ticket, tkt, review, failed_ok=False):
        """Returns True if the ticket is complete (or only the last review
        failed if ok_failed is True) and therefore actions (e.g., ticket
        changes and executing commands) should be taken.
        
        A ticket is complete when its completeness criteria is met and
        the review has PASSED and is the ticket's last review with no
        other PENDING reviews.  Completeness criteria is defined in
        trac.ini like this:
        
         completeness = phase=(codereview|verifying|releasing)
        
        The above means that the ticket's phase field must have a value
        of either codereview, verifying, or releasing for the ticket to
        be considered complete.  This helps prevent actions from being
        taken if there's a code review of partial work before the ticket
        is really ready to be fully tested and released.
        """
        # check review's completeness
        reason = review.is_incomplete(ticket)
        if failed_ok and reason and CodeReview.NOT_PASSED in reason:
            return True
        return not reason
    
    def _get_ticket_changes(self, tkt, status):
        """Return a dict of field-value pairs of ticket fields to change
        for the given ticket as defined in trac.ini.  As one workflow
        opinion, the changes are processed in order:
        
         passed = phase=verifying,owner={captain}
        
        In the above example, if the review passed and the ticket's phase
        already = verifying, then the owner change will not be included.
        """
        changes = {}
        for group in getattr(self,status,[]):
            field,value = group.split('=',1)
            if value.startswith('{'):
                value = tkt[value.strip('{}')]
            if tkt[field] == value:
                break # no more changes once ticket already has target value
            changes[field] = value
        return changes
    
    def _execute_command(self, status):
        if not self.command:
            return
        p = Popen(self.command, shell=True, stderr=STDOUT, stdout=PIPE)
        out = p.communicate()[0]
        if p.returncode == 0:
            self.log.info('command: %s' % self.command)
        else:
            self.log.error('command error: %s\n%s' % (self.command,out))


class CommitTicketReferenceMacro(WikiMacroBase):
    """This is intended to replace the builtin macro by providing additional
    code review status info for the changeset.  To use, disable the builtin
    macro as follows:
    
    [components]
    tracopt.ticket.commit_updater.committicketreferencemacro = disabled
    """
    
    def expand_macro(self, formatter, name, content, args={}):
        reponame = args.get('repository') or ''
        rev = args.get('revision')
        repos = RepositoryManager(self.env).get_repository(reponame)
        try:
            changeset = repos.get_changeset(rev)
            message = changeset.message
            
            # add review status to commit message (
            review = CodeReview(self.env, reponame, rev)
            status = review.encode(review.status)
            message += '\n\n{{{#!html \n'
            message += '<div class="codereviewstatus">'
            message += '  <div class="system-message %s">' % status.lower()
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


class ChangesetTicketMapper(Component):
    """Maintains a mapping of changesets to tickets in a codereviewer_map
    table.  Gets invoked for each changeset addition or modification."""
    
    implements(IRepositoryChangeListener)
    
    # IRepositoryChangeListener methods
    
    def changeset_added(self, repos, changeset):
        self._map(repos.reponame, changeset)
    
    def changeset_modified(self, repos, changeset, old_changeset):
        self._map(repos.reponame, changeset, update=True)
    
    def _map(self, reponame, changeset, update=False):
        # extract tickets from changeset message
        ticket_re = CommitTicketUpdater.ticket_re
        tickets = ticket_re.findall(changeset.message)
        epoch = time.mktime(changeset.date.timetuple())
        now = int(epoch * CodeReview.EPOCH_MULTIPLIER)
        
        # insert into db
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if update:
            cursor.execute("""
                DELETE FROM codereviewer_map
                WHERE repo=%s and changeset=%s;
                """, (reponame,changeset.rev))
        for ticket in tickets:
            try:
                cursor.execute("""
                    INSERT INTO codereviewer_map
                           (repo,changeset,ticket,time)
                    VALUES (%s,%s,%s,%s);
                    """, (reponame,changeset.rev,ticket,now))
            except Exception, e:
                self.log.warning("Unable to insert changeset %s/%s " +\
                    "and ticket %s into db: %s" %\
                    (changeset.rev,reponame,ticket,str(e)))
        db.commit()


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
    ticket_re = re.compile(r"ticket=(?P<id>[0-9]+)")
    path = req.environ.get('HTTP_REFERER','')
    return ticket_re.findall(path)

import re
import time

from trac.mimeview import Context
from trac.resource import ResourceNotFound
from trac.util.datefmt import pretty_timedelta
from trac.wiki.formatter import format_to_html
from trac.ticket.model import Ticket


class CodeReview(object):
    """A review for a single changeset."""
    
    # default status choices - configurable but must always be exactly three
    STATUSES = ['FAILED','PENDING','PASSED']
    DEFAULT_STATUS = STATUSES[1]
    NOT_PASSED = "(not %s)" % STATUSES[2]
    EPOCH_MULTIPLIER = 1000000.0
    
    # db schema
    db_name = 'coderev'
    db_version = 2 # see upgrades dir
    
    def __init__(self, env, repo, changeset, req=None):
        """The summary field will only get converted to html format in
        a html_summary field if a req object is provided."""
        self.env = env
        self.repo = repo
        self.changeset = changeset
        self.req = req
        self.db = self.env.get_db_cnx()
        self.statuses = self.env.config.get('codereviewer','status_choices')
        if not isinstance(self.statuses,list):
            self.statuses = self.statuses.split(',')
        self._clear()
    
    def _clear(self):
        self._status = None    # updated to latest status
        self._reviewer = None  # updated to reviewer who made latest status
        self._when = None      # updated to when status changed last
        self._tickets = None   # updated from commit message on save
        self._summaries = None
        self._changeset_when = None
    
    @property
    def status(self):
        if self._status is None:
            self._populate()
        return self._status
    
    @property
    def reviewer(self):
        if self._reviewer is None:
            self._populate()
        return self._reviewer
    
    @property
    def when(self):
        if self._when is None:
            self._populate()
        return self._when
    
    @property
    def summaries(self):
        if self._summaries is None:
            self._populate_summaries()
        return self._summaries
    
    @property
    def changeset_when(self):
        if self._changeset_when is None:
            self._populate_tickets()
        return self._changeset_when
    
    @property
    def tickets(self):
        if self._tickets is None:
            self._populate_tickets()
        return self._tickets
    
    def save(self, status, reviewer, summary, **kw):
        status = self.encode(status)
        when = int(time.time() * self.EPOCH_MULTIPLIER)
        if status == self.status and self._when != 0: # initial is special
            status = '' # only save status when changed
        if not status and not summary:
            return False # bah - nothing worthwhile to save
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO codereviewer
                   (repo,changeset,status,reviewer,summary,time)
            VALUES (%s,%s,%s,%s,%s,%s);
            """, (self.repo,self.changeset,status,reviewer,summary,when))
        self.db.commit()
        self._clear()
        return True
    
    def decode(self, status):
        if status:
            try:
                # convert from canonical to configured
                i = self.STATUSES.index(status)
                status = self.statuses[i]
            except Exception, e:
                pass
        return status
    
    def encode(self, status):
        if status:
            try:
                # convert from configured to canonical
                i = self.statuses.index(status)
                status = self.STATUSES[i]
            except Exception, e:
                pass
        return status
    
    @staticmethod
    def get_reviews(env, ticket, req=None):
        """Return all reviews for the given ticket in changeset order."""
        reviews = []
        cursor = env.get_db_cnx().cursor()
        cursor.execute("""
            SELECT repo, changeset
            FROM codereviewer_map
            WHERE ticket='%s'
            ORDER BY time ASC;
            """ % ticket)
        for repo,changeset in cursor:
            review = CodeReview(env, repo, changeset, req)
            reviews.append(review)
        return reviews
    
    def is_incomplete(self, ticket):
        """Returns False if the ticket is complete - meaning:
        
         * the ticket satisfies its completeness criteria
         * no reviews are PENDING for this ticket
         * this ticket's last review PASSED
        
        If the ticket is incomplete, then a string is returned that explains
        the reason.
        """
        # check completeness criteria
        try:
            tkt = Ticket(self.env, ticket)
            completeness = self.env.config.get('codereviewer','completeness','')
            if completeness:
                for criteria in completeness.split(','):
                    field,rule = criteria.split('=',1)
                    value = tkt[field]
                    rule_re = re.compile(rule)
                    if not rule_re.search(value):
                        return "Ticket #%s field %s=%s which violates rule %s"%\
                            (tkt.id,field,value,rule)
        except ResourceNotFound:
            pass # e.g., incorrect ticket reference
        
        # check review status
        reviews = CodeReview.get_reviews(self.env, ticket)
        if not reviews:
            return "Ticket #%s has no reviews." % ticket
        for review in reviews:
            if review.encode(review.status) == 'PENDING':
                return "Ticket #%s has a %s review for changeset %s" % \
                       (ticket,review.status,review.changeset)
        if review.encode(review.status) != 'PASSED':
            return "Ticket #%s's last changeset %s = %s %s" % \
                   (ticket,review.changeset,review.status,self.NOT_PASSED)
                   
        return False
    
    def _populate(self):
        """Populate this object from the database."""
        # get the last status change ('' status indicates no change)
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT status, reviewer, time
            FROM codereviewer
            WHERE repo='%s' AND changeset='%s' AND status != ''
            ORDER BY time DESC LIMIT 1;
            """ % (self.repo,self.changeset))
        row = cursor.fetchone() or (self.DEFAULT_STATUS,'',0)
        status,self._reviewer,self._when = row
        self._status = self.decode(status)
    
    def _populate_summaries(self):
        """Returns all summary records for the given changeset."""
        summaries = []
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT status, reviewer, summary, time
            FROM codereviewer
            WHERE repo='%s' AND changeset='%s'
            ORDER BY time ASC;
            """ % (self.repo,self.changeset))
        for status,reviewer,summary,when in cursor:
            pretty_when = time.strftime('%Y-%m-%d %H:%M',
                time.localtime(long(when) / self.EPOCH_MULTIPLIER))
            pretty_when += ' (%s ago)' % pretty_timedelta(when)
            summaries.append({
                'repo': self.repo,
                'changeset': self.changeset,
                'status': self.decode(status) or '',
                'reviewer': reviewer,
                'summary': summary,
                'html_summary': self._wiki_to_html(summary),
                'when': when,
                'pretty_when': pretty_when,
            })
        self._summaries = summaries
    
    def _populate_tickets(self):
        """Populate this object's tickets from the database."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT ticket, time
            FROM codereviewer_map
            WHERE repo='%s' AND changeset='%s';
            """ % (self.repo,self.changeset))
        self._tickets = []
        self._changeset_when = 0
        for ticket,when in cursor:
            if ticket:
                self._tickets.append(ticket)
            self._changeset_when = when
    
    def _wiki_to_html(self, message):
        if not self.req:
            return message
        ctx = Context.from_request(self.req)
        html = format_to_html(self.env, ctx, message, escape_newlines=True)
        return html.replace("'","\\'").replace('"','\\"').replace('\n','\\n')

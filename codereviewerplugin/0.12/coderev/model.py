import time
from trac.db import Table, Column, Index
from trac.mimeview import Context
from trac.util.datefmt import pretty_timedelta
from trac.wiki.formatter import format_to_html


class CodeReview(object):
    """A review for a single changeset."""
    
    EPOCH_MULTIPLIER = 1000000
    
    # db schema
    db_name = 'coderev'
    db_version = 1
    db_tables = [
        Table('codereviewer')[
            Column('repo', type='text'),
            Column('changeset', type='text'),
            Column('status', type='text'),
            Column('reviewer', type='text'),
            Column('summary', type='text'),
            Column('time', type='integer'),
            Index(columns=['repo','changeset','time']),
        ],
    ]
    
    def __init__(self, env, repo, changeset, status_default='', req=None):
        """The summary field will only get converted to html format in
        a html_summary field if a req object is provided."""
        self.env = env
        self.db = env.get_db_cnx()
        self.repo = repo
        self.changeset = changeset
        self.status_default = status_default
        self.req = req
        self._clear()
    
    def _clear(self):
        self._status = None    # updated to latest status
        self._reviewer = None  # updated to reviewer who made latest status
        self._when = None      # updated to when status changed last
        self._summaries = None
    
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
            self._populate()
        return self._summaries
    
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
        row = cursor.fetchone() or (self.status_default,'',0)
        self._status,self._reviewer,self._when = row
        self._summaries = self._get_summaries()
    
    def _get_summaries(self):
        """Returns all summary records for the given changeset."""
        summaries = []
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT status, reviewer, summary, time
            FROM codereviewer
            WHERE repo='%s' AND changeset='%s'
            ORDER BY time ASC;
            """ % (self.repo,self.changeset))
        for row in cursor:
            status,reviewer,summary,when = row
            pretty_when = time.strftime('%Y-%m-%d %H:%M',
                time.localtime(long(when) / self.EPOCH_MULTIPLIER))
            pretty_when += ' (%s ago)' % pretty_timedelta(when)
            summaries.append({
                'repo': self.repo,
                'changeset': self.changeset,
                'status': status or '',
                'reviewer': reviewer,
                'summary': summary,
                'html_summary': self._wiki_to_html(summary),
                'when': when,
                'pretty_when': pretty_when,
            })
        return summaries
    
    def _wiki_to_html(self, message):
        if not self.req:
            return message
        ctx = Context.from_request(self.req)
        html = format_to_html(self.env, ctx, message, escape_newlines=True)
        return html.replace("'","\\'").replace('"','\\"').replace('\n','\\n')
    
    def save(self, status, reviewer, summary, **kw):
        when = int(time.time()) * self.EPOCH_MULTIPLIER
        if status == self.status:
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

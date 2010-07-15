"""A simple captcha to allow anonymous ticket changes as long as the user solves
a math problem.

I thought that the ITicketManipulator prepare_ticket method would be the place
to add extra HTML stuff to the ticket page, but it seems to be for future use
only.  The only way I found that I could add to the HTML was by modifying the
Genshi template using the ITemplateStreamFilter.

I looked at http://trac-hacks.org/wiki/BlackMagicTicketTweaksPlugin for help
trying to understand how the Genshi transformation stuff worked.

Database setup borrowed from BSD licensed TicketModerator by John D. Siirola at
Sandia National Labs.  See http://trac-hacks.org/wiki/TicketModeratorPlugin

Author: Rob McMullen <robm@users.sourceforge.net>
License: Same as Trac itself
"""
import re
import random
import sys
import time
import urllib

from trac.core import *
from trac.db.schema import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter, IRequestHandler
from trac.wiki.api import IWikiPageManipulator

from genshi.builder import tag
from genshi.filters.transform import Transformer

schema = [
    # Table to hold pending math captcha elements as we wait for the web server
    # to post the results of the user's action
    Table('mathcaptcha_history', key='id')[
        Column('id', auto_increment=True), # captcha ID
        Column('ip'),                      # submitter IP address
        Column('submitted', type='int'),   # original submission time
        Column('left_operand', type='int'), # left operand
        Column('operator'),                # operator (text string, "+", "-", etc)
        Column('right_operand', type='int'), # right operand
        Column('solution', type='int'),    # solution
        Column('incorrect_solution'),      # incorrect guess
        Column('author'),                  # author of incorrect guess
        Column('summary'),                 # description included with failed guess
        Column('text'),                    # combined field including any other text typed by the spambot
        Column('href'),                    # url used in captcha
        Column('solved', type='boolean'),  # whether or not it was successfully solved
        ],
]

def to_sql(env, table):
    """ Convenience function to get the to_sql for the active connector."""
    from trac.db.api import DatabaseManager
    dm = env.components[DatabaseManager]
    dc = dm._get_connector()[0]
    return dc.to_sql(table)


class MathCaptchaPlugin(Component):
    implements(ITicketManipulator, ITemplateStreamFilter, IWikiPageManipulator,
               IEnvironmentSetupParticipant, IRequestHandler)
    
    timeout = 600 # limit of 10 minutes to process the page

    # The captcha history will be cleared after this number of days to allow
    # some postmortem as spam harvesters start to evolve
    clearout_days = 30

    # Database setup from http://trac-hacks.org/wiki/TicketModeratorPlugin
    # The current version for our portion of the database
    db_version = 2
    
    # Offset value for database id.  This is a large integer that is used to
    # modify the database row id so that the real database id is not stored
    # raw in the HTML.  Because the database ids may be small numbers, I don't
    # want the spam harvesters to simply copy fields from this hidden item
    # into the solution.
    id_offset = 5830285
    
    # Number of invalid captchas before the IP is blocked
    ban_after_failed_attempts = 4


    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        cursor = db.cursor()
        self._create_tables(cursor, self.env)
        cursor.execute( "INSERT INTO system VALUES " + \
                        "('mathcaptcha_version', '%s')"
                        % (self.db_version,) )
        db.commit()

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be 
        upgraded.  Returns `True` if upgrade is needed, `False` otherwise."""
        cursor = db.cursor()
        return self._get_version(cursor) != self.db_version

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade, but don't commit as that
        is done by the common upgrade procedure when all plugins are done."""
        cursor = db.cursor()
        ver = self._get_version(cursor)
        if ver == self.db_version:
            return
        
        if ver == 0:
            self._create_tables(cursor, self.env)
            cursor.execute( "INSERT INTO system VALUES " + \
                            "('mathcaptcha_version', '%s')"
                            % (self.db_version,) )
            # When the database is created in this manner, it will always be
            # the current schema so we can return here without going through
            # the upgrade process
            return
        
        # do database schema upgrades here...
        
        if ver == 1:
            # Version 1 of the schema used a prefix called 'incorrect_' on
            # author, summary, and text.  But version 2 of the schema stores
            # every attempt in the schema so the prefix is misleading.  The
            # prefix is therefore removed in version 2.
            table_v2 = Table('mathcaptcha_history', key='id')[
                Column('id', auto_increment=True), # captcha ID
                Column('ip'),                      # submitter IP address
                Column('submitted', type='int'),   # original submission time
                Column('left_operand', type='int'), # left operand
                Column('operator'),                # operator (text string, "+", "-", etc)
                Column('right_operand', type='int'), # right operand
                Column('solution', type='int'),    # solution
                Column('incorrect_solution'),      # incorrect guess
                Column('author'),                  # author of incorrect guess
                Column('summary'),                 # description included with failed guess
                Column('text'),                    # combined field including any other text typed by the spambot
                Column('href'),                    # url used in captcha
                Column('solved', type='boolean'),  # whether or not it was successfully solved
                ]
            cursor.execute("ALTER TABLE mathcaptcha_history RENAME TO " + \
                           "mathcaptcha_history_OLD")
            for stmt in to_sql(self.env, table_v2):
                cursor.execute(stmt)
            old_fields = ", ".join(['ip', 'submitted', 'left_operand', 'operator',
                     'right_operand', 'solution', 'incorrect_solution',
                     'incorrect_author', 'incorrect_summary', 'incorrect_text'])
            new_fields = ", ".join(['ip', 'submitted', 'left_operand', 'operator',
                     'right_operand', 'solution', 'incorrect_solution',
                     'author', 'summary', 'text'])
            cursor.execute("INSERT INTO mathcaptcha_history (%s) SELECT %s FROM mathcaptcha_history_OLD" % (new_fields, old_fields))
            cursor.execute("DROP TABLE mathcaptcha_history_OLD")
            ver += 1
        
        # Record the current version of the db environment
        cursor.execute( "UPDATE system SET value=%s WHERE "
                        "name='mathcaptcha_version'" % (ver,) )
        if ver != self.db_version:
            raise TracError("MathCaptcha failed to upgrade environment.")
    
    def _get_version(self, cursor):
        try:
            sql = "SELECT value FROM system WHERE name=" + \
                "'mathcaptcha_version'"
            self.log.debug(sql)
            cursor.execute(sql)
            return int(cursor.fetchone()[0] or 0)
        except:
            return 0

    def _create_tables(self, cursor, env):
        """ Creates the basic tables as defined by schema.
        using the active database connector. """
        for table in schema:
            for stmt in to_sql(env, table):
                cursor.execute(stmt)


    def create_math_problem(self, values):
        """Hook for generation of the math problem.
        
        As a side effect, should populate the values dict with the
        'left_operand', 'operator', 'right_operand' and 'solution' keys that
        will be placed in the database.
        
        Returns a text version of the math problem that is presented to the
        user.
        """
        values['left_operand'] = random.randint(1,10)
        values['operator'] = "add"
        values['right_operand'] = random.randint(1,10)
        values['solution'] = values['left_operand'] + values['right_operand']
        return "adding %d and %d" % (values['left_operand'], values['right_operand'])

    def get_content(self, req):
        """Returns the Genshi tags for the new HTML elements representing the
        Captcha.
        """
        values = {}
        values['ip'] = req.remote_addr
        values['submitted'] = int(time.time())
        math_problem_text = self.create_math_problem(values)
        values['author'] = req.args.get('author')
        values['summary'] = req.args.get('field_summary')
        values['text'] = self.get_failed_attempt_text(req)
        values['href'] = req.path_info
        
        # Save the problem so that the post request of the web server knows
        # which request to process.  This is required on FCGI and mod_python
        # web servers, because there may be many different processes handling
        # the request and there's no guarantee that the same web server will
        # handle both the form display and the form submit.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        fields = values.keys()
        cursor.execute("INSERT INTO mathcaptcha_history (%s) VALUES (%s)"
                       % (','.join(fields),
                          ','.join(['%s'] * len(fields))),
                       [values[name] for name in fields])
        id = db.get_last_id(cursor, 'mathcaptcha_history')
        db.commit()
        self.env.log.debug("%s %s %s%s: generating math solution: id=%d, %d %s %d = %d" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, id, values['left_operand'], values['operator'], values['right_operand'], values['solution']))
        
        # Obfuscating the names of the input variables to trick spam harvesters
        # to put other data in the solutions field.  The math solution is
        # named "email" in the hopes that it will attract email addresses
        # instead of numbers.  The database key is named "url" to try to
        # attract non-numbers
        content = tag.div()(
            tag.label('Anonymous users are allowed to post by %s ' % math_problem_text) + tag.input(type='text', name='email', class_='textwidget', size='5') + tag.input(type='hidden', name='url', value=str(id + self.id_offset))
            )
        return content
    
    def is_validation_needed(self, req):
        """Hook to determine whether or not the math captcha should be shown.
        
        Currently, only anonymous users get shown the captcha, but this could
        be modified for local purposes.
        """
        return req.authname == "anonymous"
    
    def is_banned(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT id, solved FROM mathcaptcha_history WHERE ip=%s", (req.remote_addr,) )
        failed = 0
        for row in cursor:
            if row[1] is not None and not row[1]:
                failed += 1
        return failed > self.ban_after_failed_attempts

    def validate_mathcaptcha(self, req):
        """Validates the user (or spammer) input
        
        Uses the database storage to compare the user input with the correct
        solution.
        """
        # The database key is named 'url' as described in get_content
        id = int(req.args.get('url')) - self.id_offset
        
        # Ban IP addresses after repeated failures
        if self.is_banned(req):
            self.env.log.error("%s %s %s%s: Banned after %d failed attempts" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, self.ban_after_failed_attempts))
            self.store_failed_attempt(req, id, "IP IS NOW BANNED!")
            raise RuntimeError("Too many failed attempts")
        
        # Look up previously stored data to compare the solution
        db = self.env.get_db_cnx()
        fields = ['ip', 'submitted', 'left_operand', 'operator', 'right_operand', 'solution']
        cursor = db.cursor()
        cursor.execute("SELECT %s FROM mathcaptcha_history WHERE id=%%s " %
                       ','.join(fields), (id, ))
        row = cursor.fetchone()
        if not row:
            self.env.log.error("id=%d not found in mathcaptcha_history" % (id, ))
            return [(None, "Invalid key in HTML")]
        
        values = {}
        for i in range(len(fields)):
            values[fields[i]] = row[i]

        if values['submitted'] + self.timeout < time.time():
            return [(None, "Took too long to submit page.  Please submit again.")]

        # The solution is named 'email' in the form submission as described
        # in get_content
        user_solution = req.args.get('email')
        error = self.verify_solution(req, values, user_solution)
        
        if error:
            self.store_failed_attempt(req, id, user_solution)
            
            # Only take the time to clean out the history of a failed solution,
            # because we don't care how long we take on a failure.  Success
            # should be quick, and it's not important that the history be
            # cleaned out exactly on time.
            self.clean_history()
        else:
            self.store_successful_attempt(req, id)
        
        return error

    def verify_solution(self, req, values, user_solution):
        try:
            solution = int(user_solution)
            if values['solution'] == solution:
                self.env.log.debug("%s %s %s%s: Solution: '%s' author=%s comment:\n%s" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, user_solution, req.args.get('author'), self.get_failed_attempt_text(req)))
                error = []
            else:
                self.env.log.error("%s %s %s%s: Error in math solution: %d %s %d != %s author=%s comment:\n%s" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, values['left_operand'], values['operator'], values['right_operand'], user_solution, req.args.get('author'), self.get_failed_attempt_text(req)))
                error = [(None, "Incorrect solution -- try solving the equation again!")]
        except:
            self.env.log.error("%s %s %s%s: Bad digits: '%s' author=%s comment:\n%s" % (req.remote_addr, req.remote_user, req.base_path, req.path_info, user_solution, req.args.get('author'), self.get_failed_attempt_text(req)))
            error = [(None, "Anonymous users are only allowed to post by solving the math problem at the bottom of the page.")]
        return error


    def store_failed_attempt(self, req, id, user_solution):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("UPDATE mathcaptcha_history SET incorrect_solution=%s, author=%s, summary=%s, text=%s, solved=%s WHERE id=%s", (user_solution, req.args.get('author'), req.args.get('field_summary'), self.get_failed_attempt_text(req), False, id))
        db.commit()
    
    def store_successful_attempt(self, req, id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("UPDATE mathcaptcha_history SET solved=%s WHERE id=%s", (True, id))
        db.commit()
    
    def get_failed_attempt_text(self, req):
        text = ""
        field = req.args.get('field_description')
        if field:
            text += field
        field = req.args.get('comment')
        if field:
            text += field
        return text

    def clean_history(self, days=None):
        # History after a certain number of days is cleared out
        if days is None:
            days = self.clearout_days
        older_than = time.time() - (days * 24 * 60 * 60)
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM mathcaptcha_history "
                       "WHERE submitted<%s", (older_than,))
        db.commit()

    def show_banned(self, req):
        raise RuntimeError("Too many failed attempts")

    # ITemplateStreamFilter interface

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        #self.env.log.info(filename)
        add_captcha = False
        if data['authname'] == 'anonymous':
            if self.is_banned(req):
                self.env.log.debug("%s %s %s%s: IP banned as spammer" % (req.remote_addr, req.remote_user, req.base_path, req.path_info))
                stream = tag.label("System offline.")
                return stream
                
            href = req.path_info
            self.env.log.debug(href)
            self.env.log.debug(filename)
            if filename == "ticket.html":
                if "newticket" in href:
                    add_captcha = 'TICKET_CREATE' in req.perm
                elif "ticket" in href:
                    add_captcha = 'TICKET_MODIFY' in req.perm or 'TICKET_APPEND' in req.perm
            elif filename == "wiki_edit.html":
                add_captcha = 'WIKI_MODIFY' in req.perm
        
        if add_captcha:
            # Insert the math question right before the submit buttons
            stream = stream | Transformer('//div[@class="buttons"]').before(self.get_content(req))
        return stream
    
    
    # ITicketManipulator interface
    
    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        if self.is_validation_needed(req):
            return self.validate_mathcaptcha(req)
        return []
    
    # IWikiPageManipulator interface
    
    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        """Validate a wiki page after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        if self.is_validation_needed(req):
            return self.validate_mathcaptcha(req)
        return []
    
    # IRequestHandler methods
    
    def match_request(self, req):
        return re.match(r'/mathcaptcha-(attempts|clear|successful)(?:_trac)?(?:/.*)?$', req.path_info)
    
    def process_request(self, req):
        req.perm.assert_permission('TRAC_ADMIN')
        
        matches = re.match(r'/mathcaptcha-clear(?:_trac)?(?:/.*)?$', req.path_info)
        if matches:
            self.process_clear(req)
        else:
            matches = re.match(r'/mathcaptcha-successful(?:_trac)?(?:/.*)?$', req.path_info)
            if matches:
                self.process_successful(req)
                return
        self.process_attempts(req)
    
    def process_clear(self, req):
        self.clean_history(0)
    
    def process_attempts(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/html')
        
        db = self.env.get_db_cnx()
        fields = ['ip', 'submitted', 'href', 'incorrect_solution', 'author', 'summary', 'text', 'solved']
        cursor = db.cursor()
        cursor.execute("SELECT %s FROM mathcaptcha_history ORDER BY submitted" %
                       ','.join(fields))
        html = "<table border><tr><th>%s</th></tr>\n" % "</th><th>".join(fields)
        lines = []
        for row in cursor:
            if row[-1] is not None and not row[-1]:
                lines.append("<tr><td>%s</td></tr>\n" % "</td><td>".join([str(i) for i in row]))
        html += "\n".join(lines) + "</table>"
        req.send_header('Content-length', str(len(html))) 
        req.end_headers()
        req.write(html)
    
    def process_successful(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/html')
        
        db = self.env.get_db_cnx()
        fields = ['ip', 'submitted', 'href', 'solution', 'author', 'summary', 'text', 'solved']
        cursor = db.cursor()
        cursor.execute("SELECT %s FROM mathcaptcha_history ORDER BY submitted" %
                       ','.join(fields))
        html = "<table border><tr><th>%s</th></tr>\n" % "</th><th>".join(fields[:-1])
        lines = []
        for row in cursor:
            if row[-1]:
                values = list(row[:-1])
                values[1] = time.asctime(time.localtime(values[1]))
                lines.append("<tr><td>%s</td></tr>\n" % "</td><td>".join([str(i) for i in values]))
        html += "\n".join(lines) + "</table>"
        req.send_header('Content-length', str(len(html))) 
        req.end_headers()
        req.write(html)

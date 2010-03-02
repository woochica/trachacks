# codereviewlistener.py

from email.MIMEText import MIMEText
from time import strftime, localtime
import smtplib
import re

from trac import __version__
from trac.core import Component, implements
from trac.wiki import wiki_to_html
from trac.notification import NotifyEmail, Notify

from trac.web.clearsilver import HDFWrapper
from trac.web.main import populate_hdf

from codereview.web_ui import ICodeReviewListener
from codereview.web_ui import str_status

from codereview.model import CodeReview

import xmlrpclib


class BamBooNotify:
    """BambooNotify"""
    def __init__(self, env):
        self.env = env

    def notify(self, cr_dict):
        self.cr_dict = cr_dict
        cr_id = cr_dict['cr_id']
        cr = CodeReview(self.env, cr_id)
        reviewers = ", ".join(cr.get_reviewers())
        api_key = self.env.config.get("codereview", "sender_api_key")
        xmlrpcserver = self.env.config.get("codereview", "bamboo_xmlrpc_server")
        bamboo_enabled = self.env.config.get("codereview", "bamboo_enabled")
        absurl = self.env.config.get("codereview", "absurl")
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT author from revision where rev=%s" % (str(cr_id), ))
        cs_author = cursor.fetchone()
        if cs_author:
            cs_author = cs_author[0]
        else:
            return
        if absurl.endswith("/"):
            absurl = absurl[:-1]
        if api_key and xmlrpcserver and bamboo_enabled == "true":
            try:
                server = xmlrpclib.ServerProxy(xmlrpcserver)
                server.add_update(int(api_key), \
                    "Revision %s has been reviewed by %s. %s/CodeReview/%s" % \
                                  (cr_id, reviewers, absurl, cr_id), 
                                  [cs_author,])
            except Exception, error_info:
                self.env.log.error(error_info)

class CodeReviewNotifyEmail(NotifyEmail):
    template_name = "code_review_notify_email.cs"
    from_email = "codereview@localhost"
    ticket_pattern = re.compile('#([0-9]+)')

    def __init__(self, env):
        NotifyEmail.__init__(self, env)
        self.hdf = HDFWrapper(loadpaths=self.get_templates_dirs())
        populate_hdf(self.hdf, env)

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def notify(self, cr_dict):
        self.cr_dict = cr_dict
        cr = CodeReview(self.env, cr_dict['cr_id'])
        
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute("SELECT author, message FROM revision WHERE rev='%s'" % cr_dict['cr_id'])

        recordset = cursor.fetchall()

        if not recordset:
            return
        cs_author = recordset[0][0]
        cs_message = recordset[0][1]

        if cs_author == "anonymous" and cr_dict['cr_author'] == "anonymous":
            return

        subject = "[TracNotify] ChangeSet r%s by %s reviewed by %s" % \
                  (cr_dict['cr_id'], cs_author, ','.join(cr.get_reviewers()))
        if cr_dict['priority'] == 'critical':
            subject = '[Critical]' + subject

        ticket_info = self.get_ticket_info(cs_message, cr_dict['cr_message'])

        self.hdf['trac_name'] = self.env.config.get('project', 'name')
        absurl = self.env.config.get('codereview', 'absurl')
        self.hdf['absurl'] = absurl
        self.hdf['r_content'] = wiki_to_html(cr_dict['cr_message'], self.env, cr_dict['req'], absurls = absurl)
        self.hdf['ticket_len'] = len(ticket_info)
        self.hdf['t_info'] = ticket_info
        self.hdf['cs_id'] = cr_dict['cr_id']
        self.hdf['cs_author'] = cs_author
        self.hdf['cs_message'] = wiki_to_html(cs_message, self.env, cr_dict['req'], absurls = absurl, escape_newlines=True)
        self.hdf['r_author'] = ', '.join(cr.get_reviewers())
        self.hdf['r_priority'] = cr_dict['priority']

        self.subject = subject

        self.smtp_server = self.config['notification'].get('smtp_server')
        self.smtp_port = self.config['notification'].getint('smtp_port')
        self.from_email = self.config['notification'].get('smtp_from')
        self.replyto_email = self.config['notification'].get('smtp_replyto')
        self.from_email = self.from_email or self.replyto_email
        if not self.from_email and not self.replyto_email:
            raise TracError(Markup('Unable to send email due to identity '
                                   'crisis.<p>Neither <b>notification.from</b> '
                                   'nor <b>notification.reply_to</b> are '
                                   'specified in the configuration.</p>'),
                            'SMTP Notification Error')

        # Authentication info (optional)
        self.user_name = self.config['notification'].get('smtp_user')
        self.password = self.config['notification'].get('smtp_password')

        Notify.notify(self, cr_dict['cr_id'])

    def get_reviewer_team(self):
        reviewer_team = self.env.config.get("codereview", "team_list", "")
        if reviewer_team:
            return [reviewer.strip() for reviewer in reviewer_team.split(',')]
        else:
            return []

    def get_recipients(self, cr_id):
        cr = CodeReview(self.env, cr_id)
        reviewers = list(set(self.get_reviewer_team() + cr.get_reviewers()))

	cs_author = self.hdf.get('cs_author', None)
	if cs_author is None:
            cursor = self.env.get_db_cnx().cursor()
            cursor.execute("SELECT author FROM revision WHERE rev='%s'" % cr_id)
            cs_author = cursor.fetchone()
            if cs_author:
                cs_author = cs_author[0]
            else:
	        cs_author = ''

        if cs_author in reviewers:
            reviewers.remove(cs_author)
        return ([cs_author,], reviewers)

    def get_ticket_info(self, cs_message, cr_message):
        cursor = self.env.get_db_cnx().cursor()
        ticket_ids = set(self.ticket_pattern.findall(cs_message or '') + self.ticket_pattern.findall(cr_message or ''))
        ticket_info = []
        if(ticket_ids):
            cursor.execute('SELECT id, summary FROM ticket WHERE id in (%s) ORDER BY id' % ','.join(ticket_ids))
            for id, summary in cursor.fetchall():
                ticket_info.append({'id': id, 'summary': summary})
        return ticket_info

    def send(self, torcpts, ccrcpts):
        from email.MIMEText import MIMEText
        from email.Utils import formatdate, formataddr
        body = self.hdf.render(self.template_name)
        projname = self.config.get('project', 'name')
        headers = {}
        headers['X-Mailer'] = 'Trac %s, by Edgewall Software' % __version__
        headers['X-Trac-Version'] =  __version__
        headers['X-Trac-Project'] =  projname
        headers['X-URL'] = self.config.get('project', 'url')
        headers['Subject'] = self.subject
        headers['From'] = (projname, self.from_email)
        headers['Sender'] = self.from_email
        headers['Reply-To'] = self.replyto_email

        def build_addresses(rcpts):
            """Format and remove invalid addresses"""
            return filter(lambda x: x, \
                          [self.get_smtp_address(addr) for addr in rcpts])
        def remove_dup(rcpts, all):
            """Remove duplicates"""
            tmp = []
            for rcpt in rcpts:
                if not rcpt in all:
                    tmp.append(rcpt)
                    all.append(rcpt)
            return (tmp, all)

        toaddrs = build_addresses(torcpts)
        ccaddrs = build_addresses(ccrcpts)

        recipients = []
        (toaddrs, recipients) = remove_dup(toaddrs, recipients)
        (ccaddrs, recipients) = remove_dup(ccaddrs, recipients)
        
        if len(recipients) < 1:
            self.env.log.info('no recipient for a ticket notification')
            return

        headers['To'] = ', '.join(toaddrs)
        headers['Cc'] = ', '.join(ccaddrs)
        headers['Date'] = formatdate()
        if not self._charset.body_encoding:
            try:
                dummy = body.encode('ascii')
            except UnicodeDecodeError:
                raise TracError, "CodeReview contains non-Ascii chars. " \
                                 "Please change encoding setting"
        msg = MIMEText(body)
        msg.set_type("text/html")

        del msg['Content-Transfer-Encoding']
        msg.set_charset(self._charset)
        self.add_headers(msg, headers)
        self.env.log.debug("Sending SMTP notification to %s on port %d to %s"
                           % (self.smtp_server, self.smtp_port, recipients))
        msgtext = msg.as_string()
        # Ensure the message complies with RFC2822: use CRLF line endings
        recrlf = re.compile("\r?\n")
        msgtext = "\r\n".join(recrlf.split(msgtext))
        self.server.sendmail(msg['From'], recipients, msgtext)

class CodeReviewNotify(Component):
    implements(ICodeReviewListener)

    def review_changed(self, env, cr_id, cr_message, version, cr_author, status, priority, req = None, ctime= None):
        if status == str_status['CompletelyReview']:
            if self.env.config.get("codereview", "notify_enabled") == 'true':
                CodeReviewNotifyEmail(self.env).notify(locals())
            if self.env.config.get("codereview", "bamboo_enabled") == 'true':
                BamBooNotify(self.env).notify(locals())

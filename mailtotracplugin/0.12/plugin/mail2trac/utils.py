"""utility functions for mail2trac"""

import base64
import email
import email.Utils
import re
import os
import smtplib
from trac.attachment import Attachment
from StringIO import StringIO




### Trac-specific functions

def emailaddr2user(env, addr):
    """returns Trac user name from an email address"""
    cnx = env.get_read_db()
    name, address = email.Utils.parseaddr(addr)
    toto = env.get_known_users()
    for user in env.get_known_users():
        if address == user[2]: # get_known_users return (username, name, email), we want the mail
            return user[0]


def send_email(env, from_addr, recipients, message):
    """
    BBB method for sending mail;  trunk already has a nice API;
    see http://trac.edgewall.org/browser/trunk/trac/notification.py
    """

    # options from trac.ini
    smtp_server = env.config.get('notification', 'smtp_server')
    smtp_port = int(env.config.get('notification', 'smtp_port') or 25)
    smtp_user = env.config.get('notification', 'smtp_user')
    smtp_password = env.config.get('notification', 'smtp_password')

    # ensure list of recipients
    if isinstance(recipients, basestring):
        recipients = [ recipients ]

    # send the email
    session = smtplib.SMTP(smtp_server, smtp_port)
    if smtp_user: # authenticate
        session.login(smtp_user.encode('utf-8'),
                      smtp_password.encode('utf-8'))
    session.sendmail(from_addr, recipients, message)

def add_attachments(env, ticket, attachments):
    """add attachments to the ticket"""
    ctr = 1
    if not attachments : return 
    for msg in attachments:
        attachment = Attachment(env, 'ticket', ticket.id)
        attachment.author = ticket['reporter']
        #attachment.description = ticket['summary']
        payload = msg.get_payload()
        if msg.get('Content-Transfer-Encoding') == 'base64':
            payload = base64.b64decode(payload)
        size = len(payload)
        filename = msg.get_filename() or message.get('Subject')
        if not filename:
            filename = 'attachment-%d' % ctr
            extensions = KNOWN_MIME_TYPES.get(message.get_content_type())
            if extensions:
                filename += '.%s' % extensions[0]
            ctr += 1
        buffer = StringIO()
        print >> buffer, payload
        buffer.seek(0)
        attachment.insert(filename, buffer, size)
        os.chmod(attachment.path, 0666)
        # TODO : should probably chown too

### generic email functions
    
def reply_subject(subject):
    """subject line appropriate to reply"""
    subject = subject.strip()
    return 'Re: %s' % subject

def reply_body(body, message):
    """
    body appropriate to a reply message
    """
    payload = message.get_payload(decode = True)
    if isinstance(payload, basestring):
        body += '\n\nOriginal message:\n %s' % payload
    return body

def get_body_and_attachments(message, description=None, attachments=[]):
    contents = {}
    attachments = []
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        ctype        = part.get_content_type()
        ctype = ctype.split(';')[0]
        cdisposition = part.get('content-disposition')
        cdisposition = (cdisposition or '').split(';')[0].strip()

        
        if cdisposition != 'attachment':
            
            if ctype not in ('text/plain', 'text/html'):
                continue
            
            if not contents.has_key(ctype):
                payload = part.get_payload(decode = True)
                charset = part.get_charsets('ascii')[0]
                    
                try:
                    payload = unicode(payload, charset, 'replace')
                except LookupError:
                    payload = unicode(payload, 'ISO-8859-1', 'replace')

                contents[ctype] = payload
            continue
        elif (ctype not in ('application/pgp-signature')) :
            file_name = part.get_filename()
            attachments.append(part)
    return strip_quotes(contents['text/plain']), attachments


subject_re = re.compile('( *[Rr][Ee] *:? *)*(.*)')

def strip_res(subject):
    """strip the REs from a Subject line"""
    match = subject_re.match(subject)
    return match.groups()[-1]

def strip_quotes(message):
    """strip quotes from a message string"""
    body = []
    on_regex = re.compile('On .*, .* wrote:')
    for line in message.splitlines():
        line = line.strip()
        if line.strip().startswith('>'):
            continue
        if on_regex.match(line):
            continue
        body.append(line)
    body = '\n'.join(body)
    return body.strip()


if __name__ == '__main__' :
    s = ''
    with open('/home/zitune/tmp/mail', 'r') as f :
        s = f.read()
    body, att = get_body_and_attachments(email.message_from_string(s))

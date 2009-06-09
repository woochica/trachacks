"""utility functions for mail2trac"""

import email
import email.Utils
import smtplib

def emailaddr2user(env, addr):
    """returns Trac user name from an email address"""

    name, address = email.Utils.parseaddr(addr)
    for user in env.get_known_users():
        if address == user[2]: # ?
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

    
def reply_subject(subject):
    """subject line appropriate to reply"""
    subject = subject.strip()
    return 'Re: %s' % subject

def reply_body(body, message):
    """
    body appropriate to a reply message
    """
    payload = message.get_payload()
    if isinstance(payload, basestring):
        body += '\n\nOriginal message:\n %s' % payload
    return body

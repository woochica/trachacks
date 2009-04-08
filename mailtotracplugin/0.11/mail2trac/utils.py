import email
import email.Utils

def emailaddr2user(env, addr):
    """returns Trac user name from an email address"""

    name, address = email.Utils.parseaddr(addr)
    for user in env.get_known_users():
        if address == user[2]: # ?
            return user[0]

Tested with version  0.11.2 of Trac.

Trac.ini important properties are:

[ldap]
host = 
bind_user = 
bind_passwd =
basedn = 
user_rdn = 
attempts = 1

Attempts it's a number that indicates retry connecting to the LDAP server. 
It's optional.
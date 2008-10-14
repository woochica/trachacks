Tested with version  0.11.2 of Trac.

Trac.ini important properties are:

[ldap]
host = 
bind_user = 
bind_passwd =
basedn = 
user_rdn =         [1]
attempts = 1       [2]
user_filter = uid  [2] [3] 

Attempts it's a number that indicates retry connecting to the LDAP server. 
It's optional.

[1] It is just necessary to change the password
[2] Optional fields
[3] For Active Directory use "sAMAccountName" instead "uid" 


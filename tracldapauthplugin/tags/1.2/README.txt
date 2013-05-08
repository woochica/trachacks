TracLDAPAuth
------------

An AccountManager password store that uses python-ldap to check against an
LDAP server.


Configuration Options
---------------------
host_url
	Server URL to use for LDAP authentication. e.g.:
		ldap://ldap.example.com
		ldaps://ldap.example.com

base_dn
	The user base DN when searching for users

bind_user
	LDAP user for searching

bind_password
	LDAP user password

search_scope
	The ldap search scope: base, onelevel or subtree

search_filter
	The ldap search filter template where %s is replace with the username


Example configuration
---------------------

[ldap]
host_url = ldap://ldap.example.com
base_dn = OU=Users,DC=example,DC=com
bind_user = ldap@example.com
bind_password = your_secret_password_here
search_scope = subtree
search_filter = (&(objectClass=user)(sAMAccountName=%s))


[account-manager]
password_store = LDAPStore

[components]
ldapauth.* = enabled
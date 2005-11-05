from setuptools import setup, find_packages

setup (
    name = 'LdapPlugin',
    version = "0.2.2",
    packages = find_packages(),
    package_data = { 
    },
    author = "Emmanuel Blot",
    author_email = "manu.blot@gmail.com",
    description = "LDAP extensions for Trac 0.9",
    keywords = "trac ldap permission group acl",
    url = "http://trac-hacks.swapoff.org/wiki/LdapPlugin",
)

"""Perforce version control plugin for Trac.

Enables the 'perforce' repository type in the trac.ini configuration file.

To configure the perforce plugin:

[trac]
repository_type = perforce
repository_dir = /

[perforce]
port = perforce:1666
user = p4trac
password = secret
unicode = 0
"""

__all__ = ['api', 'util']

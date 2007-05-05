"""Methods for schema upgrades."""

from compat import schema_to_sql

"""
This map contains transition function for each new schema version.
Each transition function should contain a docstring with short summary
of what's happening, they'll get printed on stdout during the
environment upgrade.
"""
map = {}

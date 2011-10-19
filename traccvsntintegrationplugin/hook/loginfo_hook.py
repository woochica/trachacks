# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import os
from CvsntLoginfo import CvsntLoginfo
from ProjectConfig import ProjectConfig

# all 'intelligence' is implemented in the CvsntLoginfo class
config = ProjectConfig()
loginfo = CvsntLoginfo(config)


# create the databases
if not os.path.exists(config.call_db):
    loginfo.db_check_create_calls()
if not os.path.exists(config.changeset_db):
    loginfo.db_check_create_changeset()
        
# retrieve raw info from the loginfo hook that is calling us 
loginfo.get_raw_info_from_hook()

# store raw info for replay/debug
loginfo.db_insert_call()

# parse raw info
loginfo.get_loginfo_from_argv()
loginfo.get_loginfo_from_stdin()

# insert changeset into the database (either insert new record or append to recent record with same commit log message)
loginfo.db_insert_append_changeset()
        
# now call trac (the cvsnt repository within trac will get the info from the record that we inserted above)
loginfo.trac_insert_changeset()

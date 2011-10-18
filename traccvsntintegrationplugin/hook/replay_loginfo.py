# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys
from CvsntLoginfo import CvsntLoginfo
from ProjectConfig import ProjectConfig

# all 'intelligence' is implemented in the CvsntLoginfo class
config = ProjectConfig()
loginfo = CvsntLoginfo(config)

callNo = -1
try:
    callNo = int(sys.argv[1])
except:
    print 'Usage: replay_loginfo <callNo>'
    sys.exit(-1)

# create the databases
createdb = False # set to false once the database file is created
if createdb:
    loginfo.db_check_create_calls()
    loginfo.db_check_create_changeset()
        
# retrieve raw info on a previous loginfo_hook call from the database
try:
    loginfo.get_raw_info_from_db(callNo)
except:
    print 'No data found for callNo #' + repr(callNo)
    sys.exit(-1)

# parse raw info
loginfo.get_loginfo_from_argv()
loginfo.get_loginfo_from_stdin()

# insert changeset into the database (either insert new record or append to recent record with same commit log message)
loginfo.db_insert_append_changeset()
        
# now call trac (the cvsnt repository within trac will get the info from the record that we inserted above)
loginfo.trac_insert_changeset()

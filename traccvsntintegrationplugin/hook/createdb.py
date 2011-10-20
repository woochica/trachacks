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

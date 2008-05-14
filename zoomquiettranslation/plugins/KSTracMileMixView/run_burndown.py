#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         run_burndown.py
# Purpose:      run burndown.py
#               to replace burndown.sh
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

import sys,os
import time
import logging

import adodb

from ini import Settings, sqltrac

VER = "run_burndown.py v1.0~080423"
cmdPY = "python"

#----------------------------------------------------------------------------
# help methods

#def toUtf8(msg):
#    if isinstance(msg, unicode):
#        msg = msg.encode("utf-8")
#    return msg

def run(runscripy, proj):
#    if isinstance(proj,unicode):
#        proj = proj.encode("utf-8")

    log("%(RUNSCRIPY)s %(PROJ)s @ " % {"RUNSCRIPY":runscripy, "PROJ":proj} + date())
    #log(runscripyPath +  proj  + today())
    cmd = "%(cmdPY)s %(RUNSCRIPY)s %(PROJ)s %(date)s" % {"cmdPY":cmdPY,
                                                        "RUNSCRIPY":runscripy, 
                                                        "PROJ":proj,
                                                        "date":date()}
    log(cmd)
    os.system(cmd)
    

def date():
    return time.strftime("%y%m%d", time.localtime(time.time()))

def today():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

def log(msg):
    print msg
    f = open(LOGFILE, "a+")
    f.write(msg + "\n")
    f.close

def stripMilestoneName(m):
    # strip milestone name
    mm = []
    for s in m.split("."):
        try:
            s.encode("ascii")
            mm.append(s)
        except:
            break
    return ".".join(mm)    

def getMilestones():
    # connect trac.db
    conn = adodb.NewADOConnection('sqlite')
    dbf = "%s/%s/%s"%(Settings['rootpath']
        ,Settings['projname']
        ,Settings['dbname'])
    conn.Connect(database = dbf) #"trac.db"

    # retrieve all milestones
    sqls = sqltrac
    reAllMilestone = [m[0] for m in conn.GetAll(sqls['allMilestone'])]
    
    # strip milestone name
    milestone = []
    for m in reAllMilestone:
        milestone.append(stripMilestoneName(m))

    print "\n"*3, "milestone", milestone
    #return ['kxedem2', 'kxewssm11', 'kxefeng1', 'kxefeng2a']
    return milestone

#----------------------------------------------------------------------------
update = ""
if len(sys.argv) > 2:
    update = sys.argv[1].decode("utf-8")

abspath = os.path.abspath(sys.argv[0])
dirname = os.path.dirname(abspath)

#----------------------------------------------------------------------------
# init milestones
allMilestones = getMilestones()
if update:
    if update not in allMilestones:
        sys.exit(1)

#----------------------------------------------------------------------------
# init settings for burndown
LOGFILE = os.path.join(dirname, "log/burndown-%(today)s.log" % {"today": today()})

# starting burndown
log("###%(VER)s::start@ " % {"VER":VER} + date())

if update:
    PROJ = update
    run(os.path.join(dirname, "burndown.py"), PROJ)
else:
    for PROJ in allMilestones:
        run(os.path.join(dirname, "burndown.py"), PROJ)

# end burndown
log("###%(VER)s::end ALL@ " % {"VER":VER} + date())

#----------------------------------------------------------------------------
# init settings for relaticket
LOGFILE = os.path.join(dirname, "log/relati-%(today)s.log" % {"today": today()})

# starting relaticket
log("###%(VER)s::start@ " % {"VER":VER} + date())

if update:
    PROJ = update
    run(os.path.join(dirname, "relaticket.py"), PROJ)
else:
    for PROJ in allMilestones:
        run(os.path.join(dirname, "relaticket.py"), PROJ)

# end relaticket
log("###%(VER)s::end ALL@ " % {"VER":VER} + date())

sys.exit(0)
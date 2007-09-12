#!/usr/bin/env python
# coding: utf-8

import commands
import sys
import os
#import pyPgSQL

from libpositrium import logger as log

# ----------------------------------
# env setting

env = {
    'svn':
        {
        'admin':'unknown',
        'repos':'/srv/svn/repos'
        },
    'trac':
        {
        'template':'/usr/share/trac/templates',
        'admin':'unknown',
        'project':'/home/trac/public_html'
        },
    'pgsql':
        {
        'create':'unknown',
        'drop':'unknown'
        }
    }
env['svn']['admin'] = commands.getoutput('which svnadmin')
env['trac']['admin'] = commands.getoutput('which trac-admin')
env['pgsql']['create'] = commands.getoutput('su - postgres -c \"which createdb\"')
env['pgsql']['drop'] = commands.getoutput('su - postgres -c \"which dropdb\"')

# ----------------------------------
# user check
def checkUser():
    if commands.getoutput('whoami') != "root":
        print log.fatal("You must be root to add new trac-project!")
        sys.exit()

def showSettings():
    BAD = "x"
    OK = "o"
    AUTO = "A"
    svn_repos_isavaile = BAD
    trac_project_isavaile = BAD
    trac_templ_isavaile = BAD

    if os.access(env['svn']['repos'], os.F_OK):
       svn_repos_isavaile = OK
    if os.access(env['trac']['project'], os.F_OK):
       trac_project_isavaile = OK
    if os.access(env['trac']['template'], os.F_OK):
       trac_templ_isavaile = OK

    print "Current settings: "
    print "A = auto detect,  o = valid path,  x = invalid path"
    print "[SVN]  "
    print "       admin:\t"+AUTO+"\t"+env['svn']['admin']
    print "       repos:\t"+svn_repos_isavaile+"\t"+env['svn']['repos']
    print "       "
    print "[TRAC] "
    print "       templ:\t"+trac_templ_isavaile+"\t"+env['trac']['template']
    print "       admin:\t"+AUTO+"\t"+env['trac']['admin']
    print "       project:\t"+trac_project_isavaile+"\t"+env['trac']['project']
    print "       "
    print "[PGSQL]"
    print "       create:\t"+AUTO+"\t"+env['pgsql']['create']
    print "       drop:\t"+AUTO+"\t"+env['pgsql']['drop']
    print "       "

# ----------------------------------
# show current project list
def showProjects():
    print ""
    print "Current Projects list: "
    if os.access(env['svn']['repos'], os.F_OK):
        print commands.getoutput('ls -l '+env['svn']['repos'])
    else:
        print log.fatal("wrong path... check env['svn']['repos'].")

    print ""

# ----------------------------------
# add sequence
def addSequence(projectname):
    # input project name
    print log.debug("projectname = "+projectname)
    if os.access(env['trac']['project']+projectname+"/README", os.F_OK):
        print ""
        print log.info("already exists project name: "+projectname)
        sys.exit()
    else:
        print log.info("adding trac project: "+projectname)
        # ----------- create metadata db
        print log.info("create db \""+projectname+"\"")
        cmd_createdb = "su - postgres -c \'"+env['pgsql']['create']+" -E UTF-8 -O trac "+projectname+" \"Database for trac project "+projectname+"\"\'"
        print log.debug(cmd_createdb)
        print commands.getoutput(cmd_createdb)
        print log.info("complete.")
        print ""
        
        # ----------- create svn repos
        print log.info("create svn repos \""+projectname+"\"")
        cmd_svnadmin = env['svn']['admin']+" create "+env['svn']['repos']+"/"+projectname
        print log.debug(cmd_svnadmin)
        print commands.getoutput(cmd_svnadmin)
        print log.info("complete.")
        print ""
        
        # ----------- create trac project
        print log.info("create trac project \""+projectname+"\"")
        cmd_tracadmin = env['trac']['admin']+" "+env['trac']['project']+"/"+projectname+" initenv "+projectname+" "
        cmd_tracadmin += "postgres://trac:trac@localhost/"+projectname+" svn "
        cmd_tracadmin += env['svn']['repos']+"/"+projectname+" "
        cmd_tracadmin += env['trac']['template']
        print log.debug(cmd_tracadmin)
        print "\033[1;32m"
	print "========================================="
        print "=BEGINS= This message output from trac =="
        print "========================================="
        print commands.getoutput(cmd_tracadmin)
        print "========================================="
        print "=FINISH= This message output from trac =="
        print "========================================="
        print "\033[0m"
        print log.info("complete.")
        print ""
        
        # ----------- set up misc.
        print log.info("setup misc..")
        chmod_path = env['trac']['project']+"/"+projectname

        cmd_misc = "chmod 777 "+chmod_path
#        print "<DBUG> "+cmd_misc
        commands.getoutput(cmd_misc)
        print commands.getstatus(chmod_path)
        cmd_misc = "chmod 777 "+chmod_path+"/log"
#        print "<DBUG> "+cmd_misc
        commands.getoutput(cmd_misc)
        print commands.getstatus(chmod_path+"/log")
        cmd_misc = "chmod 777 "+chmod_path+"/plugins"
#        print "<DBUG> "+cmd_misc
        commands.getoutput(cmd_misc)
        print commands.getstatus(chmod_path+"/plugins")
        print log.info("complete.")
        print ""

# ----------------------------------
# del sequence
def delSequence(projectname):
    # input project name
    print log.debug("projectname = "+projectname)
    print env['trac']['project']+"/"+projectname+"/README"
    if os.access(env['trac']['project']+"/"+projectname+"/README", os.F_OK):
        print log.info("removing trac project: "+projectname)
        # ----------- drop metadata db
        print log.info("drop db "+projectname)
        cmd_dropdb = "su - postgres -c \""+env['pgsql']['drop']+" "+projectname+"\""
        print log.debug(cmd_dropdb)
        print commands.getoutput(cmd_dropdb)
        print log.info("complete.")
        print ""
        
        # ----------- delete svn repos
        print log.info("delete svn repos "+projectname)
        cmd_rmrepos = "rm -rf "+env['svn']['repos']+"/"+projectname
        print log.debug(cmd_rmrepos)
        print commands.getoutput(cmd_rmrepos)
        print log.info("complete.")
        print ""
        
        # ----------- delete project dir
        print log.info("delete project dir "+projectname)
        cmd_rmproj = "rm -rf "+env['trac']['project']+"/"+projectname
        print log.debug(cmd_rmproj)
        print commands.getoutput(cmd_rmproj)
        print log.info("complete.")
        print ""
    else:
        print ""
        print log.fatal("Couldn't find project: "+projectname)
        sys.exit()
    
# ----------------------------------
# main
checkUser()
showProjects()

try:
    if sys.argv[1] == "add":
        print "please input project name:",
        addSequence(raw_input())
        #addSequence("test")
    elif sys.argv[1] == "del":
        print "please input project name:",
        delSequence(raw_input())
        #delSequence("test")
    elif sys.argv[1] == "list":
        showSettings()
    else:
        print "useage: ./ezProduceTrac.sh [ add | del | list ]"
except IndexError:
    showSettings()

sys.exit()





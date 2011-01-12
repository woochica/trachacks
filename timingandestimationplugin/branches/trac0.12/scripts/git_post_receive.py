#!/usr/bin/env python
#
# This script is run after receive-pack has accepted a pack and the
# repository has been updated.  It is passed arguments in through stdin
# in the form
#  <oldrev> <newrev> <refname>
# For example:
#  aa453216d1b3e49e7f6f98441fa56946ddcd6a20 68f7abf4e6f922807889f52bc043ecd31b79f814 refs/heads/master

# GOAL: Prevent patches that have appeared in one branch from 
#       reposting to trac when they are moved to another branch
#       (this was causing duplicate comments / time from topic branches
#       being merged into main

#  This specific script will query the repository trying to isolate what
#  in this receive is a new commit that the repository has not yet
#  seen. It does this by a big call to git rev-parse, including revs
#  that are now reachable, excluding everything else (tags, heads,
#  oldrevs).

# http://www.kernel.org/pub/software/scm/git/docs/git-rev-list.html

# Once it has isolated what is new it posts those to trac.


import os, os.path, sys,logging, getpass, optparse, re
import subprocess, threading, time, errno
from optparse import OptionParser
from subprocess import PIPE

TRAC_POST_COMMIT = "/home/ACCELERATION/russ/trac-dev/TandE/trac0.12/scripts/trac-post-commit.py"




logdir=os.getenv("LOGDIR") or "/var/log/commit-hooks"
log = logging.getLogger('gpr')

## Fn to easy working with remote processes
def capturedCall(cmd, **kwargs) :
    """Do the equivelent of the subprocess.call except
    log the stderr and stdout where appropriate."""
    p= capturedPopen(cmd,**kwargs)
    rc = p.wait()
    #this is a cheap attempt to make sure the monitors
    #are scheduled and hopefully finished.
    time.sleep(0.01)
    time.sleep(0.01)
    return rc

#be warned, if you see your pipelines hanging:
#http://old.nabble.com/subprocess.Popen-pipeline-bug--td16026600.html
#close_fds=True

## Fn to easy working with remote processes
def capturedPopen(cmd, stdin=None, stdout=None, stderr=None,
                  logger=log,cd=None,
                  stdout_level=logging.INFO,
                  stderr_level=logging.WARNING, **kwargs) :
    """Equivalent to subprocess.Popen except log stdout and stderr
    where appropriate. Also log the command being called."""
    #we use None as sigil values for stdin,stdout,stderr above so we
    # can distinguish from the caller passing in Pipe.
    if(logger):
        #if we are logging, record the command we're running,
        #trying to strip out passwords.
        logger.debug("Running cmd: %s",
                     isinstance(cmd,str) and cmd
                     or subprocess.list2cmdline([i for i in cmd
                                                 if not i.startswith('-p')]))

    if cd :
        #subprocess does this already with the cwd arg,
        #convert cd over so as not to break anyone's.
        kwargs['cwd']=cd
    p = subprocess.Popen(cmd, stdin=stdin,
                         stdout=(stdout or (logger and PIPE)),
                         stderr=(stderr or (logger and PIPE)),
                         **kwargs)
    if logger :
        def monitor(level, src, name) :
            lname = "%s.%s" % (cmd[0], name)
            if(hasattr(logger, 'name')) :
                lname = "%s.%s" % (logger.name, lname)
            sublog = logging.getLogger(lname)

            def tfn() :
                l = src.readline()
                while l != "":
                    sublog.log(level,l.strip())
                    l = src.readline()

            th = threading.Thread(target=tfn,name=lname)
            p.__setattr__("std%s_thread" % name, th)
            th.start()

        if stdout == None : monitor(stdout_level, p.stdout,"out")
        if stderr == None : monitor(stderr_level, p.stderr,"err")
    return p



def gitPopen(gitdir, cmd, **kwargs) :
    """Popen git with the given command and the git-dir given. kwargs
    are passed onwards to popen."""
    cmd = ["git","--git-dir="+gitdir] + cmd
    return capturedPopen(cmd, logger=log, **kwargs)

def find_all_refs(gitdir) :
    "Get a list of all ref names in the git database, i.e. any head or tag name"
    git = gitPopen(gitdir, ["show-ref"], stdout=PIPE)
    return set(line.split()[1] for line in git.stdout)


def new_commits(gitdir, ref_updates) :
    """For the given gitdir and list of ref_updates (an array that
    holds [oldrev,newrev,refname] arrays) find any commit that is new
    to this repo.

    This works primarily by issuing a:
    git rev-list new1 ^old1 new2 ^old2 ^refs/tags/foo ^refs/heads/bar

    This function yields commits that are new in the format:
    [hash, author, date, message]
"""
    #the set of previously reachable roots starts as a list of all
    #refs currently known, which is post-receive so we will need to
    #remove some from here. Everything left will become ^refs.
    prev_roots = find_all_refs(gitdir)
    log.debug("Found %s named refs", len(prev_roots))

    #open the rev-list process and make a writer function to it.
    grl = gitPopen(gitdir, ["rev-list","--reverse", "--stdin",
			    "--pretty=tformat:%an <%ae>%n%ci%n%s%n%+b"],
		   stdin=PIPE, stdout=PIPE)
    def w(ref) : grl.stdin.write(ref + "\n")

    for (old,new,ref) in ref_updates :
	#branch deletion: newval is 00000, skip the ref, leave it in
	#the list of prev_roots
	if re.match("^0+$",new) : continue

	#Include the newrev as now reachable.
	w(new)

	#a ref that is being updated should be removed from the
	#previous list and ...
	prev_roots.discard(ref)
	#instead write out the negative line directly. However, if it
	#is a new branch (denoted by all 0s) there is no negative to
	#include for this ref.
	if re.search("[1-9]",old) :
	    w("^" + old)
	else :
	    log.info("New ref %r", ref)


    log.debug("After discarding updates, writing %s prev_roots",
	      len(prev_roots))
    #write lines for (not reachable from anything else')
    for ref in prev_roots : w("^" + ref)
    grl.stdin.close()

    ### this is a little parser for the format
    #commit <hash>
    #<Author>
    #<Date>
    #<msg>
    #<blank line>
    commit = None
    msg = ""
    def finish() :
	commit.append(msg[:-1]) #-1 to strip one \n from the pair.
	log.info("New commit: %r", commit)
	return commit

    while True :
	line = grl.stdout.readline()
	#blank line and exit code set, we're done here.
	if line == '' and grl.poll() != None :
	    if commit: yield finish()
	    log.debug("Exiting loop: %s", grl.poll())
	    break

	m = re.match("commit ([0-9a-f]+)$", line)
	if m :  #start of a new commit
	    if commit: yield finish()
	    log.debug("Starting new commit: %s", m.group(1))
	    hash = m.group(1)
	    author = grl.stdout.readline().strip()
	    date = grl.stdout.readline().strip()
	    commit = [hash,author,date]
	    msg = grl.stdout.readline()
	else :
	    msg += line

def post(commits, gitdir, cname, trac_env) :
    for [rev,author,date,msg] in commits :
	#this subprocess uses python logging with the same formatter,
	#so tell it not to log, and pass through our streams and its
	#logging should just fall in line.
        log.debug("Posting %s to trac", rev)
        capturedCall(["python", TRAC_POST_COMMIT,
                           "-p", trac_env or "",
                           "-r", rev,
                           "-u", author,
                           "-m", msg,
                           cname],
                          logger=None,
                          stdout=sys.stdout,
                          stderr=sys.stderr)

def process(gitdir, cname, trac_env, ref_updates) :
    log.info("Push by %r; CNAME: %r, TRAC_ENV: %r, updating %s refs",
	     getpass.getuser(), cname, trac_env, len(updates))

    post(new_commits(gitdir,ref_updates), gitdir, cname, trac_env)
    log.info("Finished commit hook loop, git-post-receive")



#################################################################
#### Runtime control

parser = OptionParser(""" """)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
		  help="Show more verbose log messages.")


if __name__ == "__main__":
    (options, args) = parser.parse_args()

    #when run as a hook the directory is the git repo.
    #either /var/git/ServerManagement.git
    #or     /var/git/ServerManagement/.git
    gitdir = os.getcwd()

    cname = os.getenv("CNAME")
    if cname == None :
	if len(args) >= 1 :
	    cname = args.pop(0)
	else :
	    #strip off .git if it is bare or /.git if it is a checkout.
	    cname = re.sub("/?\.git$","", gitdir)
	    cname = os.path.basename(cname)
    TRAC_ENV = os.getenv("TRAC_ENV") or os.path.join("/var/trac/",cname)

    #### Logging configuration
    log.setLevel(logging.DEBUG)
    ## log verbosely to a file
    logfile=os.path.join(logdir, "%s.git-post-receive.log" % cname)
    fh = logging.FileHandler(logfile,mode='a')
    fh.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)-8s %(message)s',
				      datefmt='%Y%m%d %H:%M:%S'))

    ## and to standard error keep the level higher
    sh = logging.StreamHandler()
    sh.setLevel(options.verbose and logging.DEBUG or logging.INFO)
    sh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)-8s %(message)s",
				      datefmt='%H:%M:%S'))

    log.addHandler(sh)
    log.addHandler(fh)
    log.info("----- git-post-receive.py -----")

    #Where will we be posting to?
    if not os.path.exists(TRAC_ENV) :
        logging.warn("None existant trac_env: %s", TRAC_ENV)
        TRAC_ENV = None
    #actually read the ref updates from stdin
    updates = [line.split() for line in sys.stdin]
    process(gitdir, cname, TRAC_ENV, updates)

# # The MIT License

# # Copyright (c) 2010 Acceleration.net

# # Permission is hereby granted, free of charge, to any person obtaining a copy
# # of this software and associated documentation files (the "Software"), to deal
# # in the Software without restriction, including without limitation the rights
# # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# # copies of the Software, and to permit persons to whom the Software is
# # furnished to do so, subject to the following conditions:

# # The above copyright notice and this permission notice shall be included in
# # all copies or substantial portions of the Software.

# # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# # THE SOFTWARE.

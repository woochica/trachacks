#!/bin/env python

from loader import *
import os
import sys
import re


PROPERTIES= ['svn:log', 
             'svn:eol-style', 
             'svn:executable', 
             'svn:keywords', 
             'svn:mime-type', 
             'svn:needs-lock', 
             'svn:externals',
             'svn:ignore', ]


def run_command(command):
    """
    This function tries to run a command on to the sistem
    and returnes a tuple composed from the exit status and 
    the output of the command.
    
    @param command: list
    @return: (int, String)
    """
    status= 0
    response= ''
    try :
        child_in, child_out_err = os.popen4(' '.join(command))
        response_list= child_out_err.readlines()
        if len(response_list) != 0 : 
            response= '\n'.join(response_list)
    except Exception:
        status= 4
        response= "Error in invoking the command "
    return (status, response)

def build_author_command(repos, rev):
    """
    This function returnes the command used for getting the
    author for a, in progress, svn commit.
    
    @param repos: String
    @param rev: int
    @return: list
    """
    global SVNLOOK
    return [SVNLOOK, '-r', str(rev), 'author', str(repos)]

def user_author_policy(author, user, property_name, settings):
    if not settings['SVN_PROPERTY'] :
        return True

    if author == user and property_name == 'svn:log' :
        return True
    
    return False

def get_trac_path(link):
    """
    This function determines the target of a symlink.
    
    @return: String
    @param link: String
    """
    hook_file= os.readlink(link)
    return os.path.sep.join(hook_file.split(os.path.sep)[:-2])

if __name__ == "__main__":
    
    #######################################
    # STEP 1 - Read and parse the ARGUMETS
    #######################################
    arguments= sys.argv[1:]
    # process the parameters
    
    if len(arguments) < 4 :
        sys.stderr.write("wrong number of arguments!" + str(arguments))
        sys.exit(1)
        
    repos= arguments[0]
    if not os.path.isdir(repos) :
        sys.stderr.write("the svn repository isn't set properly")
        sys.exit(2)
    
    # revision number
    try :
        rev= int(arguments[1])
    except ValueError:
        sys.stderr.write("bad revision number")
        sys.exit(3)
    
    # user
    user= arguments[2]
    propname= arguments[3]
    try :
        PROPERTIES.index(propname)
    except :
        sys.stderr.write("bad property name")
        sys.exit(4)
    #############################################
    # STEP 2 - Get the Trac ini SETTINGS
    #############################################
    # read the ini file of the trac enviroment
    config= api.IniReader(get_trac_path(__file__))
    
    #############################################
    # STEP 3 - Try to get the log message
    ############################################# 
    # make the command
    command= build_author_command(repos, rev)
    # run it
    status, response= run_command(command)
    response= response.strip()
    
    if status != 0 :
        sys.stderr.write("the author name couldn't be retrieved!")
        sys.exit(status)
    
    author= response
    
    ################################################
    # STEP 4 - Try to verify the author
    ################################################
    if user_author_policy(author, user, propname, config.get_svn_policy_settings()) :
        status= 0
    else :
        sys.stderr.write("modifing this property isn't conform to the project policy!")
        status= 1
    
    ################################################################
    # STEP 5 - Exit the Hook 
    ################################################################

    sys.exit(status)
# Copyright (C) 2008-2009 NAV CANADA (http://www.navcanada.ca)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Mike Stoddart <stoddam@navcanada.ca>

import os, sys, pwd, grp, fileinput
from stat import *
from config import *

def delete_directory(top):
	for root, dirs, files in os.walk(top, topdown=False):
	    for name in files:
	        os.remove(os.path.join(root, name))
	    for name in dirs:
	        os.rmdir(os.path.join(root, name))

def get_apache():
	# Determine the uid/gid for the Apache user.
	names = ["apache", "http", "apache2"]
	data = []
	
	for username in names:
		try:
			data = pwd.getpwnam("apache")
			break
		except KeyError, e:
			# Didn't find this name, skip it and try the next one.
			pass

	if len(data) == 0:
		print "Couldn't find the configured Apache user, exiting"
		sys.exit(-3)
	
	return data[2], data[3]

def check_owner():
	"""
	Debug function used to retrieve and display the uid/gid for the
	Apache user/process. Verifies that the discovery logic works.
	"""
	# Determine the uid/gid for the Apache user.
	uid, gid = get_apache()

def set_ownership(top):
	# Determine the uid/gid for the Apache user.
	uid, gid = get_apache()
	
	#print "Resetting directory ", top
	os.chown(top, uid, gid)
				
	# Change the owner of the destination to match.
	for root, dirs, files in os.walk(top, topdown=False):
		for name in files:
			#print "Resettng file = ", os.path.join(root, name)
			os.chown(os.path.join(root, name), uid, gid)
		for name in dirs:
			#print "Resetting directory ", os.path.join(root, name)
			os.chown(os.path.join(root, name), uid, gid)

def sed_file(fn, project_name):
	# This will replace all instances of <project_name> with the specfied name.
	for lines in fileinput.FileInput(fn, inplace=1): ## edit file in place
		lines = lines.replace("<project_name>", project_name)
		sys.stdout.write(lines)

def get_confirmation(msg):
	resp = raw_input(msg + " (yes/Yes/YES): ")
	if resp in ["YES", "yes", "Yes"]:
		return True
	else:
		return False
		
	return False

def create_password_file(delete=False):
	# Does the password file exist?
	if not os.path.isfile(PASSWORD_FILE):
		# Create the empty password file.
		f = open(PASSWORD_FILE, "w")
		f.close()

		# Give ownsership of the password file to Apache.
		set_ownership(PASSWORD_FILE)
	else:
		# It does exist. Should we delete it and re-create it?
		if delete:
			# Delete password as requested.
			delete_password_file()
			
			# Re-create it. Recursion!
			create_password_file()

def delete_password_file():
	# Delete the password file.
	os.remove(PASSWORD_FILE)

def check_password_file():
	# Does the password file exist?
	if not os.path.isfile(PASSWORD_FILE):
		# Create the file.
		create_password_file()

def get_project_list():
	projects = []
	
	print "Enter a list of unix project names separated by commas with no whitespace."
	csl = raw_input("Or enter a single unix project name: ")
	
	# Remove whitespace.
	csl = csl.replace(" ", "")
	
	# Now convert the string into an array of unix project names.
	projects = csl.split(",")
	
	# Force each project name to be lowercase.
	project_list = []
	for project in projects:
		project_list.append(project.lower())
	
	return project_list

def demote_user(username):
	projects = get_project_list()
	for project_name in projects:
		# Demote the user.
		print "Demoting " + username + " from " + project_name
		s = "trac-admin " + os.sep + ROOT_PATH + os.sep + "trac" + os.sep + \
			project_name + " permission remove " + username + " TRAC_ADMIN"
		print "Executing " + s
		os.system(s)

def promote_user(username):
	svn_root = ROOT_PATH + os.sep + "svn"
	trac_root = ROOT_PATH + os.sep + "trac"
	
	# Ensure the password file exists.
	check_password_file()

	print
	print "Promoting user to admin status"
	print
	projects = get_project_list()
	print
	
	for project_name in projects:
		print "Promoting user " + username + " for project " + project_name
		# Promote the user.
		s = "trac-admin " + os.sep + trac_root + os.sep + \
			project_name + " permission add " + username + " TRAC_ADMIN"
		os.system(s)

		if VERIFY_USER_PERMISSIONS:
			# Verify the new status.
			s = "trac-admin " + os.sep + trac_root + os.sep + \
				project_name + " permission list " + username
			os.system(s)

def get_unix_username():
	# Request a unix username.
	print
	username = raw_input("Enter the user's unix name: ")
	print
	
	# Force it to be lowercase.
	return username.lower()

def user_exists(username):
    # Check to see if this user already exists in the .htpasswd file.
    f = open(PASSWORD_FILE, "r")
    found = False
    for line in f:
        if line.find(username) > -1:
            found = True
            break

    f.close()
    return found

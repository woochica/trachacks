# Copyright (C) 2008-2009 NAV CANADA (http://www.navcanada.ca)
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Mike Stoddart <stoddam@navcanada.ca>
# Author: Jeff Dever <deverj@navcanada.ca>

import os, sys, pwd, grp, re, fileinput, shutil, getpass
from stat import *
from config import *

# Set to True to enable verbose output
verbose = False 

 
def delete_directory(top):
	"""Delete a directory tree rooted at top."""
	for root, dirs, files in os.walk(top, topdown=False):
	    for name in files:
	        os.remove(os.path.join(root, name))
	    for name in dirs:
	        os.rmdir(os.path.join(root, name))

def get_apache():
	"""Determine the uid/gid for the Apache user."""
	names = ["apache", "http", "httpd", "apache2"]
	data = []
	
	for username in names:
		try:
			data = pwd.getpwnam(username)
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
	"""Sets the ownership of a directory tree rooted at top."""
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
	"""This will replace all instances of <project_name> with the specfied name."""
	for lines in fileinput.FileInput(fn, inplace=1): ## edit file in place
		lines = lines.replace("<project_name>", project_name)
		sys.stdout.write(lines)

def prompt_confirmation(msg):
	"""Prompt user with msg for yes/no answer and return True/False."""
	resp = raw_input(msg + " (yes/no): ").lower()
	if resp in ["yes", "y"]:
		return True
	elif resp in ["no", "n"]:
		return False
		
	return prompt_confirmation(msg)

def init_trac(trac_root):
	"""Create the Trac directory and copy in any default files."""
	print "Creating directory for Trac environments in %s"%trac_root
	mkdirs(trac_root)

def init_svn(svn_root):
	"""Create the svn directory and copy in any default files."""
	print "Creating directory for Subversion repositories in %s"%svn_root
	mkdirs(svn_root)

def init_conf(conf_root):
	"""Create the configuration directory and copy in any default files."""
	print "Creating configuration directory in %s"%conf_root 
	mkdirs(conf_root)
	copy_file("%s/conf/project.template"%INSTALL_DIR, conf_root)
	copy_file("%s/conf/trac.conf"%INSTALL_DIR, HTTPD_CONF_ROOT)
	create_file(get_password_file())

	service_enable(HTTPD_SERVICE)
	service_command(HTTPD_SERVICE, "start")	

def init_postgres(db_root):
	"""Initialize a postgres database in the given db_root."""

	#if there is an existing datastore, use it, otherwise create one
	if os.path.exists(db_root):
		print "Using existing datastore in %s"%db_root
	else:
		if os.path.isdir(DB_DEFAULT):
			print "Moving existing datastore from %s"%DB_DEFAULT
			shutil.move(DB_DEFAULT, db_root)
		else:
			print "Creating new datastore in %s"%db_root
			mkdirs(db_root)

	# if there is an existing default database, use it, symlink to it
	if os.path.exists(DB_DEFAULT):
		print "Using existing %s"%db_root
	else:
		print "Creating simlink in %s"%DB_DEFAULT
		os.symlink(db_root, DB_DEFAULT)
	
	service_enable(DB_SERVICE)
	service_command(DB_SERVICE, "start")

	#TODO: it would be nice if we could pass the password if it is defined
	cmd = "%s -u postgres %s --no-superuser --createdb --createrole --echo --pwprompt %s"%(SUDO, CREATEUSER, DB_USER)
	os.system(cmd);
	
	hba_conf = "%s/data/pg_hba.conf"%db_root
	print "Adding an authentication entry to %s"%hba_conf
	print "NOTE: you may still need to edit this file to remove other authorisations!"
	file_append(hba_conf, "# local entry to allow trac to talk to the database on the same server")
	file_append(hba_conf, "host\tall\tall\t127.0.0.1/32\tmd5")

	service_command(DB_SERVICE, "reload")


def destroy_all(root_path):
	"""Destroys the entire configuration and data directory tree for the root_path."""
	print "You asked for it..."

	# Stop services.
	service_command(DB_SERVICE, "stop")
	service_command(HTTPD_SERVICE, "stop")

	# Delete files.
	try:
		print "Deleting the directory tree ..."
		shutil.rmtree(root_path, ignore_errors=False)
		print "The dirty deed is done (dirt cheap)"
	except OSError:
		print "Failed to remove some files from %s" % root_path
		return False
	
	return True	

def create_file(file, delete=False):
	"""Creates the file if it does not exist.  If it does exist and delete
	is true the file is deleted and then re-created."""
	if not os.path.isfile(file):
		# Create the empty file.
		f = open(file, "w")
		f.close()

		# Give ownsership of the file to Apache.
		set_ownership(file)
	else:
		# It does exist. Should we delete it and re-create it?
		if delete:
			# Delete file as requested.
			os.remove(file)
			
			# Re-create it. Recursion!
			create_file(project)

def prompt_password(confirm=False):
	"""Prompt for a password.
	If confirm then will prompt twice to check for a password match."""
	input1 = getpass.getpass("Enter password: ")
	if confirm:
		input2 = getpass.getpass("Re-type password: ")
		if input1 != input2:
			print "Passwords don't match."
			return prompt_password(confirm)

	return input1


def set_password(user, password=None):
	"""Set the password for the specified user on the given project.
	If the user doesn't exist, they will be added.
	If the project is None, the password is set globally.
	If the password is None, one will be prompted for.
	"""
	if verbose: print "set_password(%s, %s)" % (user, password)

	# compose the command to prompt if no password is given
	password_file = get_password_file()
	if password == None:
		cmd = "%s %s %s" % (HTPASSWD, password_file, user)
	else:
		cmd = "%s -b %s %s '%s'" % (HTPASSWD, password_file, user, password)

	# run the command and check the results
	status = os.system(cmd) / 256
	if status == 0: 
		#success
		return True
	elif status == 1: 
		print "file access problem"
	elif status == 2:
		print "syntax error in parameters"
	elif status == 3: 
		print "passwords don't match"
		return set_password(user)
	elif status == 4: 
		print "operation interrupted"
	elif status == 5: 
		print "value is too long"
		return set_password(user)
	elif status == 6: 
		print "illegal characters"
		return set_password(user)
	elif status == 7:
		print "password file is invalid"
	else: 
		print "unknown erorr %i" % status

	return False

def change_password(user, password):
	"""Change the password for the user on the given projects."""
	return set_password(user, password)

def add_user(user, password=None):
	"""Add a user if they don't already exist."""
	if verbose: print "add_user(%s, %s)" % (user, password)
	if user in get_user_list():
		print "User %s already exists, ignoring"%user
		return False

	if not set_password(user, password):
		print "Failed to set password for user %s"%user
		return False
	else:
		#Success.
		return True


def remove_user(user):
	"""Remove a user from the from the password file and all auth groups.
	"""
	success = True

	#Remove authentication
	if user in get_user_list():
		password_file = get_password_file()
		cmd = "%s -D %s %s" % (HTPASSWD, password_file, user)	
		status = os.system(cmd) / 256
		if (status != 0):
			print "Failed to remove user %s from %s"%(user, password_file)
			success = False
	else:
		print "User %s does not exist the the password file"%user

	#Remove all authorisations
	group_list = get_auth_group_list()
	project_list = get_project_list()
	for project in project_list:
		if not remove_auth_groups(project, user, group_list):
			print "Failed to remove user from auth group"
			success = False

	return success

def prompt_project(show_available=False, restrict_available=False, restrict_not_available=False):
	"""Prompt the user for a project name.
	The input must match the project regular expression as defined in config.py.
	show_available show the current list as part of the prompt
	restrict_available restrict the input to an item in the available list
	restrict_not_available restrict the input to an item not already in the available list
	"""
	full_list = get_project_list()

	if show_available:
		full_list.sort()
		print "Current projects: ", full_list

	input = raw_input("Enter the project's unix name: ").strip()
	regex = re.compile(PROJECT_RE)
	if not regex.match(input):
		print "Input does not match pattern %s" % PROJECT_RE
		return prompt_project(False, restrict_available, restrict_not_available)
	elif restrict_available and input not in full_list:
		print "Project %s is not a current project" % input
		return prompt_project(True, True, restrict_not_available)
	elif restrict_not_available and input in full_list:
		print "There is already a project named %s" % input
		return prompt_project(True, restrict_available, True)

	return input

def prompt_project_list(show_available=True, restrict_available=False):
	"""Prompt the user for a list of projects.
	show_available show the current list as part of the prompt
	restrict_available restrict the prompted list to available list
	"""
	full_list = get_project_list()
	# Show the current projects if requested
	if show_available:
		full_list.sort()
		print "Current projects: ", full_list
 
	# Request the input and split on whitespace into a list
	input = raw_input("Enter a list of project names: ")
	input_list = input.split()

	# Check the input list and only add well formed inputs to the list
	project_list = []
	regex = re.compile(PROJECT_RE)
	for item in input_list:
		item = item.strip()
		if not regex.match(item):
			print "Not allowing '%s': does not match pattern %s" % (item, PROJECT_RE)
		elif restrict_available and item not in full_list:
			print "Not allowing '%s': not in available list" % item
		else:
			if verbose: print "Allowing '%s'" % item
			project_list.append(item)

	return project_list

def get_project_list(user=None):
	"""Returns a list of available projects."""
	full_list = os.listdir(TRAC_ROOT)
	if user != None:
		short_list = []
		for project in full_list:
			if user_in_project(project, user):
				short_list.append(project)
		return short_list
	else:
		return full_list

def user_in_project(project, user):
	filename = "%s/%s.htpasswd"%(CONF_ROOT, project)
	if verbose: print "checking file %s for %s"%(filename, user)
	file = open(filename, "r")
	lines = file.readlines()
	file.close()

	for line in lines:
		tokens = line.split(":", 2)
		if tokens[0] == user: 
			return True

	return False
	

def get_trac_project_path(project):
	"""Returns the absolute path to a trac project directory."""
	return "%s/%s" % (TRAC_ROOT, project)

def demote_user(user, project_list, verify=False):
	"""Removes the admin permission for the user on the list of projects."""
	success = True
	for project in project_list:
		project_path = get_trac_project_path(project)
		print "Demoting %s from project %s" % (user, project)

		cmd = "%s %s permission remove %s TRAC_ADMIN" % (TRACADMIN, project_path, user)
		status = os.system(cmd) / 256
		if status != 0:
			print "Error demoting user"
			success = False

		if verify:
			# Verify the new status.
			cmd = "%s %s permission list %s" % (TRACADMIN, project_path, user)
			os.system(cmd)

	return success 

def promote_user(user, project_list, verify=False):
	"""Adds the admin permission for the user on the list of projects."""
	success = True
	for project in project_list:
		project_path = get_trac_project_path(project)
		print "Promoting %s for project %s" % (user, project)

		cmd = "%s %s permission add %s TRAC_ADMIN" % (TRACADMIN, project_path, user)
		status = os.system(cmd) / 256
		if status != 0:
			print "Error promoting user"
			success = False

		if verify:
			# Verify the new status.
			cmd = "%s %s permission list %s" % (TRACADMIN, project_path, user)
			os.system(cmd)

	return success

def prompt_username():
	"""Prompt the user for a usernamename.
	The input must match the user regular expression as defined in config.py.
	"""
	input = raw_input("Enter a username: ").strip()
	regex = re.compile(USER_RE)
	if not regex.match(input):
		print "Input does not match pattern %s" % USER_RE
		return prompt_username()

	return input

def prompt_user_list(show_available=True, restrict_available=False):
	"""Prompts the user for a list of users.
	show_available show the current list as part of the prompt
	restrict_available restrict the prompted list to available list
	"""
	full_list = get_user_list()
	# Show the current users if requested
	if show_available:
		full_list.sort()
		print "Current users: ", full_list
 
	# Request the input and split on whitespace into a list
	input = raw_input("Enter a list of user names that match pattern '%s': " % USER_RE)
	input_list = input.split()

	# Check the input list and only add well formed users to the list
	user_list = []
	for item in input_list:
		item = item.strip()
		regex = re.compile(USER_RE)
		if not regex.match(item):
			print "Not allowing '%s': does not match pattern" % item
		elif restrict_available and item not in full_list:
			print "Not allowing '%s': not in available list" % item
		else:
			if verbose: print "Allowing '%s'" % item
			user_list.append(item)

	return user_list

def get_user_list():
	"""Returns the list of users."""
	list = []
	try:
		password_file = get_password_file()
		FILE = open(password_file, "r")
		for line in FILE:
			line_tokens = line.split(":")
			if len(line_tokens) == 2:
				list.append(line_tokens[0])
		FILE.close()
	except IOError:
		print "Error reading password file '%s'" % password_file

	return list

def get_auth_group_list():
	"""Get the allowed list of auth groups."""
	#Defined these here and not in config.py since they are explicitly 
	#in the apache conf files.
	return ['trac-user', 'svn-ro', 'svn-rw', 'download']

def prompt_auth_group_list(show_available=True, restrict_available=False):
	"""Prompt the user for a list of auth groups.
	show_available show the current list as part of the prompt
	restrict_available restrict the prompted list to available list
	returns the list input by the user
	"""
	full_list = get_auth_group_list()
	# Show the current users if requested
	if show_available:
		full_list.sort()
		print "Current groups: ", full_list 
 
	# Prompt for the list as input
	input = raw_input("Enter a list of groups that match pattern '%s': " % GROUP_RE)
	input_list = input.split()

	# Check the input list and only add well formed inputs to the list
	group_list = []
	for item in input_list:
		item = item.strip()
		regex = re.compile(GROUP_RE)
		if not regex.match(item):
			print "Not allowing '%s': does not match pattern" % item
		elif restrict_available and item not in full_list:
			print "Not allowing '%s': not in available list" % item
		else:
			if verbose: print "Allowing '%s'" % item
			group_list.append(item)

	return group_list

def read_group_file(filename):
	"""Create a map of groups and users from the given filename.
	raises IOErrror
	returns map with the group as the key and a list of users as the value
	"""
	map = dict()
	if os.path.exists(filename):
		FILE = open(filename, "r")
		for line in FILE:
			line_tokens = line.split(":")
			if len(line_tokens) != 2:
				#Skip any malformed lines.
				continue
			key = line_tokens[0].strip()
			list = line_tokens[1].split()

			#Build the map of group->user_list
			list.sort()
			map[key] = []
			for item in list:
				item = item.strip()
				map[key].append(item)
	else:
		if verbose: print "Creating new file %s" % filename	
		FILE = open(filename, "w")

	FILE.close()
	return map
	
def write_group_file(map, filename):
	""" Writes the group for the given map and filename.
	#raises IOError
	#returns nothing
	"""
	FILE = open(filename, "w")
	for key in map.keys():
		FILE.write(key + ':')	
		list = map[key]
		list.sort()
		for item in list:
			FILE.write(" " + item)
		FILE.write("\n")
	FILE.close()

def get_group_file(project):
	"""Gets the absolute file path to the group file for the project."""
	return "%s/%s.group" % (CONF_ROOT, project)

def get_password_file():
	"""Gets the absolute file path to the password file.
	Ensures that the file exists."""
	password_file = "%s/htpasswd"%CONF_ROOT
	if verbose: print "password_file %s" % password_file

	#Check for existance and create it if it doesn't exist.
	if not os.path.isfile(password_file):
		print "creating password file %s" % password_file
		create_file(password_file)
	return password_file

def add_auth_groups(project, user, group_list):
	"""Adds the user to the specified groups for the given project.
	returns True on success, False on failure
	"""
	# Track changes
	changed = False

	# Read the existing auth group map from file
	try:
		filename = get_group_file(project)
		map = read_group_file(filename)
	except IOError:
		print "Error reading file '%s'" % filename
		return False
	
	# For each group, add the user to the map
	for group in group_list:
		if not group in map:
			map[group] = []
			changed = True
		if not user in map[group]:
			if verbose: print "Added %s from %s on %s" % (user, group, project)
			map[group].append(user)
			changed = True

	# Write the file back if it has changed
	try:
		if changed:
			write_group_file(map, filename)
		else:
			if verbose: print "Group map has not changed, skipping"
	except IOError:
		print "Error writing file '%s'" % filename
		return False

	return True

def remove_auth_groups(project, user, group_list):
	"""Removes the user to the specified groups for the given project.
	returns True on success, False on failure
	"""
	# Track changes
	changed = False
	
	# Read the existing auth group map from file
	try:
		filename = get_group_file(project)
		map = read_group_file(filename)
	except IOError:
		print "Error reading file '%s'" % filename
		return False
	
	# For each group, remove the user from the map
	for group in group_list:
		if group in map and user in map[group]:
			print "Removed %s from %s on %s" % (user, group, project)
			map[group].remove(user)
			changed = True

	# Write the file back if it has changed
	try:
		if changed:
			write_group_file(map, filename)
		else:
			if verbose: print "Group map has not changed, skipping"
	except IOError:
		print "Error writing file '%s'" % filename
		return False

	return True

def user_exists(user):
	"""Return true if the user exists."""
	return user in get_user_list()

def file_contains(file, str):
	"Returns true if the file contains the given string, ignoring whitespace."""
	try:
		FILE = open(file, "r")
		for line in FILE:
			if line.rstrip() == str.rstrip():
				return True
		FILE.close()
	except IOError:
		return False

	return False


def svn_remove_mirror(url, file=SVN_MIRRORS_FILE):
	"""
	Remove the specified SVN mirror url from the mirrors file.
	Return True on success, False on failure.
	"""
	if not os.path.isfile(file):
		print "\tMirror file " + file + " does not exist"
		return False

	if not file_contains(file, url):
		print "\tMirror file " + file + " does not contain " + url
		return False

	FILE = open(file, "r")
	lines = FILE.readlines()
	FILE.close()

	FILE = open(file, "w")
	for line in lines:
		if line.rstrip() == url.rstrip():
			print "\tRemoving mirror " + url 
		else:
			FILE.write(line)
	return True

def svn_add_mirror(url, file=SVN_MIRRORS_FILE):
	"""Add a new mirror to the mirror list file.
	Return True on success, False on failure.
	"""

	if not os.path.isfile(file):
		print "\tCreating file " + file 

	elif file_contains(file, url):
		print "\tFile already contains " + url
		return False

	print "\tWriting mirror " + url 
	FILE = open(file, "a")
	FILE.write(url + "\n")
	FILE.close();

	# Set ownership to apache.
	set_ownership(file)

	return True

def mkdirs(dir):
	"""Creates a directory with all parents, a la 'mkdir -p'
	and sets the ownership to the apache user."""
	if not os.path.isdir(dir):
		if verbose: print "\tCreating directory " + dir
		os.makedirs(dir)
		set_ownership(dir)
		return True
	else:
		print "\t" + dir + " already exists, ignoring"
		return False
	

def copy_file(src, dest):
	"""Copy file from src to dest, which can be a filename or directory
	and sets the ownership to the apache user."""
	shutil.copy2(src, dest)
	set_ownership(dest)

def service_enable(service):
	"""Enable the given service using the chkconfig utility."""
	cmd = "%s %s on" % (CHKCONFIG, service)
	os.system(cmd)

def service_command(service, operation):
	"""Invoke an operation the given service using the service utility."""
	cmd = "%s %s %s" % (SERVICE, service, operation)
	os.system(cmd)

def init_repo(repo_path):
	"""Initialize a SVN repository."""
	if os.path.exists(repo_path):
		print "The repository " + repo_path + " already exists"
		return False
	mkdirs(SVN_ROOT)

	#run the create command as apache
	uid, gid = get_apache()
	cmd = "%s -H -u \#%s %s create %s" % (SUDO, str(uid), SVNADMIN, repo_path)
	if verbose: print cmd
	status = os.system(cmd)
	if status == 0:
		return True
	else:
		print "Failed to create repository %s" % repo_path
		return False

def enable_revprop_change(repo_path):
	"""Adds the revprop-change hook to an SVN repository."""
	src = "%s/hooks/pre-revprop-change" % INSTALL_DIR
	dest = "%s/hooks/pre-revprop-change" % repo_path
	shutil.copy2(src, dest)
	set_ownership(dest)


def svnsync_init(source_project_url, mirror_project_url):
	"""Initialize an svnsync mirror repository."""
	options = "--non-interactive --no-auth-cache"
	credentials = "--username " + SVNSYNC_USERNAME + " --password " + SVNSYNC_PASSWORD
        cmd = "%s initialize %s %s %s %s" % (SVNSYNC, options, credentials, mirror_project_url, source_project_url)
	if verbose: print cmd
	status = os.system(cmd)
	if status == 0:
		return True
	else:
		print "Failed to initialize %s to %s" % (source_project_url, mirror_project_url)
		return False

def svnsync(project):
	"""Perform an svnsync to update all mirrors."""
	options = "--non-interactive --no-auth-cache"
	credentials = "--username " + SVNSYNC_USERNAME + " --password " + SVNSYNC_PASSWORD
	mirror_url = "file://%s/repos/%s" % (SVN_ROOT, project)
        cmd = "%s synchronize %s %s %s" % (SVNSYNC, options, credentials, mirror_url)
	if verbose: print cmd
	status = os.system(cmd)
	if status == 0:
		return True
	else:
		print "Failed to svnsycn %s" % (project)

		return False

def svn_init_mirror(source_url, mirror_url, project):
	"""Initialize an svncync mirror repository for a particular project."""
	#init the repo
	repo_path = SVN_ROOT + os.sep + project
	if not init_repo(repo_path):
		print "Run this on the mirror, not on the server"
		return False

	#make sure the svnsync user exists
	set_password(SVNSYNC_USERNAME, SVNSYNC_PASSWORD)

	#pre-revprop-change hook
	enable_revprop_change(repo_path)

	#init the synch
	if not svnsync_init(source_url + '/' + project, mirror_url + '/' + project):
		print "Mirror was not initialized"
		return False
	
	return True

def svn_add_hook_file(src, dest, project):
	"""Adds a hook file specified as src to the given project."""
	print "Adding hook '%s'" % dest

	if os.path.exists(dest):
		if verbose: print "Hook script already exists"
	else:
		if os.path.exists(src):
			if verbose: print "Copying '%s' to '%s'" % (src, dest)
			shutil.copy2(src, dest)
		else:
			print "Failed to find " + src
			return False

		if verbose: print "Set ownership and permissions"
		set_ownership(dest)
		os.chmod(dest, 0755)

	return True

def svn_remove_hook_file(hook):
	"""Remove a svn hook script given by the full path to hook."""
	print "Removing hook '%s'" % (hook)

	if os.path.exists(hook):
		try:
			os.remove(hook)
			return True
		except OSError, e:
			print "Error removing file"
			return False
	else:
		if verbose: print "File '%s' does not exist" % hook

	return True
	
def file_append(file, str):
	"""Appends a string to a file with a trailing newline."""
	if verbose: print "Appending '%s' to file '%s'" % (str, file)
	FILE = open(file, "a")
	FILE.write(str + '\n')
	FILE.close()

def file_contains(file, str):
	"""Returns true if the file contains a given string."""
	FILE = open(file, "r")
	contents = FILE.read()
	FILE.close()

	if contents.find(str) >= 0:
		return True
	else:
		return False


def file_remove(file, str):
	"""Removes a string from the given file."""
	FILE = open(file, "r")
	lines = FILE.readlines()
	FILE.close()

	FILE = open(file, "w")
	for line in lines:
		if not line.find(str) >= 0:
			FILE.write(line)
	FILE.close()

def svn_add_hook_script(project, hook, script, script_args, remove=False):
	"""Add a hook script to a particular project.
	The hook will be removed if remove is true.
	"""
	#add the script if it does not exist
	script_src = "%s/hooks/%s" % (INSTALL_DIR, script)
	script_dest = "%s/%s/hooks/%s" % (SVN_ROOT, project, script)
	if remove:
		if not svn_remove_hook_file(script_dest):
			return False

	else:
		if not svn_add_hook_file(script_src, script_dest, project):
			return False

	#add the hook if needed
	hook_src = "%s/hooks/%s" % (INSTALL_DIR, hook)
	hook_dest = "%s/%s/hooks/%s" % (SVN_ROOT, project, hook)
	if not remove:
		if not svn_add_hook_file(hook_src, hook_dest, project):
			return False

	#ensure hook calls the script
	if remove:
		if file_contains(hook_dest, script_dest):
			file_remove(hook_dest, script_dest)
		else:
			if verbose: print "Hook does not call the script"
	else:
		if file_contains(hook_dest, script_dest):
			if verbose: print "Hook already calls the script"
		else:
			file_append(hook_dest, script_dest + " " + script_args)

	return True

def project_exists(project):
	"""Return true if the project exists."""
	dir = SVN_ROOT + os.sep + project
	if verbose: print "Check for project in '%s'" % dir
	return os.path.exists(dir)

def svn_add_sync_hook(project, remove=False):
	"""Add the synchronize_mirrors.sh script for the specified project.
	If remove is true, the hook is removed instead."""
	hook = "post-commit"
	script =  "synchronize-mirrors.sh"
	script_args = "$REPOS &"
	if not svn_add_hook_script(project, hook, script, script_args, remove):
		return False

	return True

def svn_add_trac_hooks(project, remove=False):
	"""Adds the trac pre and post commit scripts for the specified project.
	If remove is true, the hook is removed instead.
	"""
	#add the trac pre-commit script
	hook = "pre-commit"
	script =  "trac-pre-commit-hook"
	script_args = "%s/%s \"`%s log -t $TXN $REPOS`\" || exit 1"% (TRAC_ROOT, project, SVNLOOK)
	if not svn_add_hook_script(project, hook, script, script_args, remove):
		return False

	#add the trac post-commit script
	hook = "post-commit"
	script =  "trac-post-commit-hook"
	script_args = "-p %s/%s -r $REV &" % (TRAC_ROOT, project)
	if not svn_add_hook_script(project, hook, script, script_args, remove):
		return False

	return True

def svn_add_email_hook(project, email, remove=False):
	"""Add the commit email script for the specified project.
	If remove is true, the hook is removed instead.
	"""
	hook = "post-commit"
	script =  "commit-email.pl"
	script_args = "\"$REPOS\" \"$REV\" %s &" % email
	if not svn_add_hook_script(project, hook, script, script_args, remove):
		return False

	return True

def get_project_conf(project=None):
	"""Returns the conf file for the given project or the conf root directory
	if the project is None or unspecified."""
	if project == None:
		return CONF_ROOT
	else:
		return CONF_ROOT + os.sep + project + ".conf"

def get_project_template():
	"""Returns the path of the local project template file."""
	template = "%s/conf/project.template"%CONF_ROOT
	if os.path.exists(template):
		return template
	else:
		return "%s/conf/project.template"%INSTALL_DIR

def delete_project_conf(project):
	"""Delete the configuration files for the given project."""
	print "Deleting apache project configuration" 
	delete_file(get_project_conf(project))
	delete_file(get_group_file(project))

def delete_file(filename):
	"""Delete the specified file.
	Traps exceptions and returns True on success.
	"""
	if not os.path.exists(filename):
		print "\tFile '%s' not found, ignoring" % filename
		return False

	try:
		os.remove(filename)
	except OSError, e:
		print "\tUnable to remove '%s': file may be locked" % filename
		return False

	return True

	

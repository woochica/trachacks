#!/usr/bin/env python
#
#  hot-backup.py: perform a "hot" backup of a Berkeley DB repository.
#                 (and clean old logfiles after backup completes.)
#
#  Subversion is a tool for revision control. 
#  See http://subversion.tigris.org for more information.
#    
# ====================================================================
# Copyright (c) 2000-2006 CollabNet.  All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.  The terms
# are also available at http://subversion.tigris.org/license-1.html.
# If newer versions of this license are posted there, you may use a
# newer version instead, at your option.
#
# This software consists of voluntary contributions made by many
# individuals.  For exact contribution history, see the revision
# history and logs, available at http://subversion.tigris.org/.
# ====================================================================

######################################################################

import sys, os, getopt, shutil, string, re

######################################################################
# Global Settings

verbose = False

# Path to svnlook utility
svnlook = "/usr/bin/svnlook"

# Path to svnadmin utility
svnadmin = "/usr/bin/svnadmin"

# Number of backups to keep around (0 for "keep them all")
num_backups = 64

# Archive types/extensions
archive_map = {
  'gz'  : ".tar.gz",
  'bz2' : ".tar.bz2",
  'zip' : ".zip"
  }

######################################################################
# Command line arguments

def usage(out = sys.stdout):
  scriptname = os.path.basename(sys.argv[0])
  out.write(
"""USAGE: %s [OPTIONS] REPOS_PATH BACKUP_PATH

Create a backup of the repository at REPOS_PATH in a subdirectory of
the BACKUP_PATH location, named after the youngest revision.

Options:
  --archive-type=FMT Create an archive of the backup. FMT can be one of:
                       bz2 : Creates a bzip2 compressed tar file.
                       gz  : Creates a gzip compressed tar file.
                       zip : Creates a compressed zip file.
  --help      -h     Print this help message and exit.

""" % (scriptname,))


try:
  opts, args = getopt.gnu_getopt(sys.argv[1:], "h?", ["archive-type=", "help"])
except getopt.GetoptError, e:
  print >> sys.stderr, "ERROR: %s\n" % e
  usage(sys.stderr)
  sys.exit(2)

archive_type = None

for o, a in opts:
  if o == "--archive-type":
    archive_type = a
  elif o in ("-h", "--help", "-?"):
    usage()
    sys.exit()

if len(args) != 2:
  print >> sys.stderr, "ERROR: only two arguments allowed.\n"
  usage(sys.stderr)
  sys.exit(2)

# Path to repository
repo_dir = args[0]
repo = os.path.basename(os.path.abspath(repo_dir))

# Where to store the repository backup.  The backup will be placed in
# a *subdirectory* of this location, named after the youngest
# revision.
backup_dir = args[1]

# Added to the filename regexp, set when using --archive-type.
ext_re = ""

# Do we want to create an archive of the backup
if archive_type:
  if archive_map.has_key(archive_type):
    # Additionally find files with the archive extension.
    ext_re = "(" + re.escape(archive_map[archive_type]) + ")?"
  else:
    print >> sys.stderr, "Unknown archive type '%s'.\n\n" % archive_type
    usage(sys.stderr)
    sys.exit(2)


######################################################################
# Helper functions

def comparator(a, b):
  # We pass in filenames so there is never a case where they are equal.
  regexp = re.compile("-(?P<revision>[0-9]+)(-(?P<increment>[0-9]+))?" +
                      ext_re + "$")
  matcha = regexp.search(a)
  matchb = regexp.search(b)
  reva = int(matcha.groupdict()['revision'])
  revb = int(matchb.groupdict()['revision'])
  if (reva < revb):
    return -1
  elif (reva > revb):
    return 1
  else:
    inca = matcha.groupdict()['increment']
    incb = matchb.groupdict()['increment']
    if not inca:
      return -1
    elif not incb:
      return 1;
    elif (int(inca) < int(incb)):
      return -1
    else:
      return 1

######################################################################
# Main

if verbose: print "Beginning hot backup of '"+ repo_dir + "'."


### Step 1: get the youngest revision.

infile, outfile, errfile = os.popen3(svnlook + " youngest " + repo_dir)
stdout_lines = outfile.readlines()
stderr_lines = errfile.readlines()
outfile.close()
infile.close()
errfile.close()

youngest = string.strip(stdout_lines[0])
if verbose: print "Youngest revision is", youngest


### Step 2: Find next available backup path

backup_subdir = os.path.join(backup_dir, repo + "-" + youngest)

# If there is already a backup of this revision, then append the
# next highest increment to the path. We still need to do a backup
# because the repository might have changed despite no new revision
# having been created. We find the highest increment and add one
# rather than start from 1 and increment because the starting
# increments may have already been removed due to num_backups.

regexp = re.compile("^" + repo + "-" + youngest +
                    "(-(?P<increment>[0-9]+))?" + ext_re + "$")
directory_list = os.listdir(backup_dir)
young_list = filter(lambda x: regexp.search(x), directory_list)
if young_list:
  young_list.sort(comparator)
  increment = regexp.search(young_list.pop()).groupdict()['increment']
  if increment:
    backup_subdir = os.path.join(backup_dir, repo + "-" + youngest + "-"
                                 + str(int(increment) + 1))
  else:
    backup_subdir = os.path.join(backup_dir, repo + "-" + youngest + "-1")

### Step 3: Ask subversion to make a hot copy of a repository.
###         copied last.

if verbose: print "Backing up repository to '" + backup_subdir + "'..."
err_code = os.spawnl(os.P_WAIT, svnadmin, "svnadmin", "hotcopy", repo_dir, 
                     backup_subdir, "--clean-logs")
if err_code != 0:
  print >> sys.stderr, "Unable to backup the repository."
  sys.exit(err_code)
else:
  if verbose: print "Done."


### Step 4: Make an archive of the backup if required.
if archive_type:
  archive_path = backup_subdir + archive_map[archive_type]
  err_msg = ""

  if verbose: print "Archiving backup to '" + archive_path + "'..."
  if archive_type == 'gz' or archive_type == 'bz2':
    try:
      import tarfile
      tar = tarfile.open(archive_path, 'w:' + archive_type)
      tar.add(backup_subdir, os.path.basename(backup_subdir))
      tar.close()
    except ImportError, e:
      err_msg = "Import failed: " + str(e)
      err_code = -2
    except tarfile.TarError, e:
      err_msg = "Tar failed: " + str(e)
      err_code = -3

  elif archive_type == 'zip':
    try:
      import zipfile
      
      def add_to_zip(baton, dirname, names):
        zp = baton[0]
        root = os.path.join(baton[1], '')
        
        for file in names:
          path = os.path.join(dirname, file)
          if os.path.isfile(path):
            zp.write(path, path[len(root):])
          elif os.path.isdir(path) and os.path.islink(path):
            os.path.walk(path, add_to_zip, (zp, path))
            
      zp = zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED)
      os.path.walk(backup_subdir, add_to_zip, (zp, backup_dir))
      zp.close()
    except ImportError, e:
      err_msg = "Import failed: " + str(e)
      err_code = -4
    except zipfile.error, e:
      err_msg = "Zip failed: " + str(e)
      err_code = -5


  if err_code != 0:
    print >> sys.stderr, \
          "Unable to create an archive for the backup.\n" + err_msg
    sys.exit(err_code)
  else:
    if verbose: print "Archive created, removing backup '" + backup_subdir + "'..."
    shutil.rmtree(backup_subdir)

### Step 5: finally, remove all repository backups other than the last
###         NUM_BACKUPS.

if num_backups > 0:
  regexp = re.compile("^" + repo + "-[0-9]+(-[0-9]+)?" + ext_re + "$")
  directory_list = os.listdir(backup_dir)
  old_list = filter(lambda x: regexp.search(x), directory_list)
  old_list.sort(comparator)
  del old_list[max(0,len(old_list)-num_backups):]
  for item in old_list:
    old_backup_item = os.path.join(backup_dir, item)
    if verbose: print "Removing old backup: " + old_backup_item
    if os.path.isdir(old_backup_item):
      shutil.rmtree(old_backup_item)
    else:
      os.remove(old_backup_item)

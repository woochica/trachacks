#!/usr/bin/env python

#os.popen("sudo -S mkdir /madewithpython", 'w').write("safety1")#
import os
import sys

args = sys.argv
short_name = args[1]
long_name = args[2]
username = args[3]

#sudo password#
password = "passwordhere"

output = [1,2,3,4,5,6]

strpath = "sudo svnadmin create /svn/repos/" + short_name 
output[1] = os.popen (strpath, 'w').write(password)

strpath = "sudo chown -R www-data /svn/repos/" + short_name
output[2] = os.popen (strpath, 'w')

strpath = "sudo trac-admin /trac/" + short_name + " initenv '" + long_name + "' 'sqlite:db/trac.db' 'svn' '/svn/repos" + short_name + "' --inherit=/etc/trac.ini"
output[3] = os.popen (strpath, 'w')

strpath = "sudo chown -R www-data /trac/" + short_name
output[4] = os.popen (strpath, 'w')

strpath = "sudo trac-admin /trac/" + short_name + " permission add " + username + " TRAC_ADMIN permission list " + username
output[5] =os.popen (strpath, 'w')

print "Results!\n\n";
f = open('run_log.log','w')
f.write(str(output[1])) % "%s<br>%s"
f.write(str(output[2])) + "<br>"
f.write(str(output[3])) + "<br>"
f.write(str(output[4])) + "<br>"
f.write(str(output[5])) + "<br>"
f.close
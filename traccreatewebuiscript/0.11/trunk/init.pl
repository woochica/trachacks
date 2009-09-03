#!/usr/bin/perl -w
$sName = $ARGV[0];
$lName = $ARGV[1];
if ($lName eq "") {
   $lName = $sName;
}
$sName =~ tr/A-Z/a-z/;
$path = "sudo svnadmin create /svn/$sName";
system ($path);
$path = "sudo chown -R www-data /svn/$sName";
system ($path);
$path = "sudo trac-admin /trac/$sName initenv '$lName' 'sqlite:db/trac.db' 'svn' '/svn/$sName' --inherit=/etc/trac.ini";
system ($path);
$path = "sudo chown -R www-data /trac/$sName";
system ($path);
$path = "sudo trac-admin /trac/$sName permission add yourusername TRAC_ADMIN permission list yourusername";
system ($path);
print "Done!\n\n";
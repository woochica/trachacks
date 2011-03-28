#! /usr/bin/perl 

use strict;
use warnings;
use English;

$OUTPUT_AUTOFLUSH=1;

my $trac_path = '';
my $db_name = 'trac';
my $db_host = 'localhost';
my $db_user = 'trac';
my $db_pass = 'tractor';

sub verbose;
my $verbose = 0;

while ( my $arg = shift @ARGV ) {
	( $arg =~ /^\-v/ ) && ( $verbose = 1 );
	( $arg =~ /^\-db/ ) && ( $db_name = shift @ARGV );
	( $arg =~ /^\-dh/ ) && ( $db_host = shift @ARGV );
	( $arg =~ /^\-du/ ) && ( $db_user = shift @ARGV );
	( $arg =~ /^\-dp/ ) && ( $db_pass = shift @ARGV );
	( $arg !~ /^\-/ ) && ( $trac_path = $arg );
}

unless ( $trac_path ) {
	print <<EOF;
$PROGRAM_NAME {options} [path-to-trac-instance]
	-v		verbose
  	-db {name}	name of the MySQL database
	-dh {hostname}	hostname of the database server
	-du {user}	username for this database
	-dp {pass} 	password for this database
EOF
	exit 1;
}
die "$trac_path doesn't appear to be a trac environment" 
	unless ( -d $trac_path and -r "$trac_path/db/trac.db" ); 
use DBI;
die "DBD::mysql needs to be installed." unless ( grep { $_ eq 'mysql' } DBI->available_drivers );
die "DBD::SQLite needs to be installed." unless ( grep { $_ eq 'SQLite' } DBI->available_drivers );


my $dsn = "DBI:mysql:database=$db_name";
my $dbh = DBI->connect($dsn, $db_user, $db_pass ) or 
	die "cannot connect to trac at $dsn as $db_user: " . $DBI::errstr;

my $sqlite_db = "$trac_path/db/trac.db";
my $sqlite = DBI->connect("dbi:SQLite:dbname=$sqlite_db") or 
	die "cannot open $sqlite_db: $!";

#-- convert an sqlite database to mysql
open IN , " echo .dump | sqlite3 $trac_path/db/trac.db |";
select IN; $INPUT_RECORD_SEPARATOR=";\n";
select STDERR; $OUTPUT_AUTOFLUSH=1;
select STDOUT;

my $tables = {};
my $str;
while ( my $cmd = <IN> )  {


	#-- skip transaction lines.
	next if $cmd =~ /BEGIN\s+TRANSACTION|COMMIT/i;

	my $table;
	if ( ($table) = ( $cmd =~ /CREATE TABLE \"?(\w+)/ ) ) {
		#-- get columns
		my ($columns_txt) = ( $cmd =~ /\((.*)\)/s );
		$columns_txt =~ s/,[^,]+unique \(.*\)//ig;
		my @columns = split(/,/,$columns_txt);
		for my $column ( @columns ) {
			my ($name, $type) =  ( $column =~ /^\s*(\w+)\s(\w+)/ );
			push @{$tables->{$table}->{'columns'}} , { 'name' => $name, 'type' => $type};
		}
		
		#-- use InnoDB for transaction support
		$cmd =~ s/;/ ENGINE=InnoDB;/;
		#-- change id's to int's and make them autoincrement
		$cmd =~ s/\sid text/ id integer AUTO_INCREMENT PRIMARY KEY/g;
		$cmd =~ s/\sid integer PRIMARY KEY/ id integer AUTO_INCREMENT PRIMARY KEY/g;
		#-- cause sqlite reports int for int64
		$cmd =~ s/\s((?:time|due|completed)) integer/$1 bigint/g; 
		#-- fix key length for text/blob 
		$cmd =~ s/((?:name|action|field|tagspace|tag|rev|source|dest|cookie|ipnr|type)) text/$1 VARCHAR(64)/g;
		$cmd =~ s/(rev) text/$1 VARCHAR(20)/g;
		$cmd =~ s/((?:node_type|change+type)) text/$1 VARCHAR(1)/g;
		$cmd =~ s/((?:sid|path|filename)) text/$1 VARCHAR(128)/g;
		# $cmd =~ s/((?:s?id)) text/$1 VARCHAR(256)/g;
		verbose STDERR "creating $table with " . join(',',map { $_->{'name'} } @{$tables->{$table}->{'columns'}}) . "\n";
		$dbh->do("DROP TABLE IF EXISTS  $table;") or die "can't drop $table \nERROR: " . $dbh->errstr;
		$dbh->do($cmd) or die "can't create table $table from\n----\n$cmd\n----\nERROR: " . $dbh->errstr;
	} 

}
close IN;


#-- now pull actual data using defined separator
for my $table ( sort keys %{$tables} ) {
	my @column_names = map { $_->{'name'} } @{$tables->{$table}->{'columns'}};
	verbose "loading table $table ..";
	my $count = 0;
	my $sth = $sqlite->prepare('select ' . join(',', @column_names) . " from $table;" );
	$sth->execute;

	while ( my @cdata = $sth->fetchrow_array ) {
		$count++;
		verbose "." if ( ($count/20) == int($count/20) );
		my $insert = "INSERT IGNORE INTO $table (" . 
			join( ',', @column_names ) .
			") VALUES(" . join(',', (map {'?' } @column_names ) ) .
			");";
		$dbh->do($insert,undef,@cdata) or 
			die "cant insert data at line $count\n----\n$insert\n----\n -" . join("\n -",@cdata) . "\n-----\nERROR:" . $dbh->errstr;
	}

	verbose "Done.\n";
}
			 
			
sub verbose {
	print STDERR @_ if $verbose;	
}
		

	
	
	




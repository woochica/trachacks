DROP TABLE trac_users;

CREATE TABLE trac_users (
	envname text NOT NULL , 
	username text NOT NULL ,
	password text NOT NULL ,
	email text ,
	UNIQUE (envname, username)
);



DROP TABLE trac_cookies;

CREATE TABLE trac_cookies (
	envname text NOT NULL ,
	cookie text NOT NULL ,
	username text NOT NULL ,
	ipnr text NOT NULL ,
	unixtime int NOT NULL 
);



DROP TABLE trac_permissions;

CREATE TABLE trac_permissions (
	envname text NOT NULL ,
	username text NOT NULL ,
	groupname text NOT NULL 
);

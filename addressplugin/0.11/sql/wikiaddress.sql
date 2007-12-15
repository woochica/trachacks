CREATE TABLE IF NOT EXISTS `wikiaddress` (
  `name` text NOT NULL,
  `location` varchar(255) default NULL,
  `address` text,
  `lat` decimal(10,6),
  `long` decimal(10,6),
  `ele` smallint(5) unsigned default 0,
  `time` int(11) default NULL,
  `author` text,
  `ipnr` text,
  PRIMARY KEY  (`name`(166),`location`(50)),
  KEY `keylat` (`lat`),
  KEY `keylong` (`long`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

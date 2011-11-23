-- phpMyAdmin SQL Dump
-- version 3.3.2deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Nov 23, 2011 at 11:09 AM
-- Server version: 5.1.41
-- PHP Version: 5.3.2-1ubuntu4.10

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Table structure for table `groups`
--

CREATE TABLE IF NOT EXISTS `groups` (
  `groupid` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `groupname` varchar(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  PRIMARY KEY (`groupid`),
  UNIQUE KEY `groupid` (`groupid`),
  UNIQUE KEY `groupname` (`groupname`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=6 ;

-- --------------------------------------------------------

--
-- Table structure for table `membership`
--

CREATE TABLE IF NOT EXISTS `membership` (
  `userid` int(10) unsigned NOT NULL,
  `groupid` int(10) unsigned NOT NULL,
  PRIMARY KEY (`userid`,`groupid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `userid` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET latin1 COLLATE latin1_bin NOT NULL,
  `password` text CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  PRIMARY KEY (`userid`),
  UNIQUE KEY `userid` (`userid`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=17 ;


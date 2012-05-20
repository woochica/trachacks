-- phpMyAdmin SQL Dump
-- version 3.3.7deb5build0.10.10.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: May 20, 2012 at 10:25 AM
-- Server version: 5.1.49
-- PHP Version: 5.3.3-1ubuntu9.5

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `trac`
--

-- --------------------------------------------------------

--
-- Table structure for table `easypoll`
--

CREATE TABLE IF NOT EXISTS `easypoll` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `poll_id` varchar(255) COLLATE utf8_bin NOT NULL,
  `poll_identifier` varchar(255) COLLATE utf8_bin NOT NULL,
  `poll_type` varchar(255) COLLATE utf8_bin NOT NULL DEFAULT 'single',
  `poll_title` varchar(255) COLLATE utf8_bin NOT NULL,
  `poll_options` text COLLATE utf8_bin NOT NULL,
  `poll_votes` text COLLATE utf8_bin NOT NULL,
  `poll_creator` varchar(255) COLLATE utf8_bin NOT NULL,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `poll_id` (`poll_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

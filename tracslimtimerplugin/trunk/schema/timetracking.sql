-- phpMyAdmin SQL Dump
-- version 2.9.1
-- http://www.phpmyadmin.net
-- 
-- Host: localhost
-- Generation Time: Apr 26, 2007 at 12:21 PM
-- Server version: 5.0.27
-- PHP Version: 5.2.0
-- 
-- Database: `timetracking`
-- 
CREATE DATABASE `timetracking` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;
USE `timetracking`;

-- --------------------------------------------------------

-- 
-- Table structure for table `tasks`
-- 

CREATE TABLE `tasks` (
  `task_id` int(10) unsigned NOT NULL auto_increment COMMENT 'The unique key for this task',
  `src_id` bigint(20) unsigned default NULL COMMENT 'The ID of this task in the source (e.g. SlimTimer)',
  `name` varchar(255) collate utf8_unicode_ci default NULL COMMENT 'A textual summary of this task',
  `tags` varchar(255) collate utf8_unicode_ci default NULL COMMENT 'Any tags (metadata) for this task',
  `owner` varchar(255) collate utf8_unicode_ci NOT NULL COMMENT 'The owner of this task',
  `created` datetime default NULL COMMENT 'The time when the task was created',
  `updated` datetime default NULL COMMENT 'The time when this task was last updated',
  `time_worked` bigint(20) unsigned default NULL COMMENT 'The total time worked on this task in seconds',
  `time_estimated` bigint(20) unsigned default NULL COMMENT 'Time estimated for this task in seconds',
  `completed_on` datetime default NULL COMMENT 'The time when this task was completed (NULL if not completed)',
  PRIMARY KEY  (`task_id`),
  KEY `src_id` (`src_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci COMMENT='Tasks for recording time against';

-- --------------------------------------------------------

-- 
-- Table structure for table `times`
-- 

CREATE TABLE `times` (
  `time_id` int(10) unsigned NOT NULL auto_increment COMMENT 'The unique key for this time entry',
  `src_id` bigint(20) unsigned default NULL COMMENT 'The ID of this entry in the source (e.g. SlimTimer)',
  `user` varchar(255) collate utf8_unicode_ci NOT NULL COMMENT 'Some string identifying the user (e.g. the trac username)',
  `start_time` datetime default NULL COMMENT 'The start of this time slice',
  `end_time` datetime default NULL COMMENT 'The end of this time slice',
  `duration` bigint(20) unsigned default NULL COMMENT 'The duration of this time slice in seconds',
  `tags` varchar(255) collate utf8_unicode_ci default NULL COMMENT 'Tags (metadata) for this time slice',
  `comments` text collate utf8_unicode_ci COMMENT 'A comment about this time slice',
  `task_id` int(10) unsigned default NULL COMMENT 'Link to task',
  PRIMARY KEY  (`time_id`),
  KEY `start_time` (`start_time`),
  KEY `user` (`user`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci COMMENT='Recorded time slices';

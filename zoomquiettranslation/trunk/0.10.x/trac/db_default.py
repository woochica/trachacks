# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2006 Edgewall Software
# Copyright (C) 2003-2005 Daniel Lundin <daniel@edgewall.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Daniel Lundin <daniel@edgewall.com>

from trac.db import Table, Column, Index

# Database version identifier. Used for automatic upgrades.
db_version = 20

def __mkreports(reports):
    """Utility function used to create report data in same syntax as the
    default data. This extra step is done to simplify editing the default
    reports."""
    result = []
    for report in reports:
        result.append((None, report[0], report[2], report[1]))
    return result


##
## Database schema
##

schema = [
    # Common
    Table('system', key='name')[
        Column('name'),
        Column('value')],
    Table('permission', key=('username', 'action'))[
        Column('username'),
        Column('action')],
    Table('auth_cookie', key=('cookie', 'ipnr', 'name'))[
        Column('cookie'),
        Column('name'),
        Column('ipnr'),
        Column('time', type='int')],
    Table('session', key=('sid', 'authenticated'))[
        Column('sid'),
        Column('authenticated', type='int'),
        Column('last_visit', type='int'),
        Index(['last_visit']),
        Index(['authenticated'])],
    Table('session_attribute', key=('sid', 'authenticated', 'name'))[
        Column('sid'),
        Column('authenticated', type='int'),
        Column('name'),
        Column('value')],

    # Attachments
    Table('attachment', key=('type', 'id', 'filename'))[
        Column('type'),
        Column('id'),
        Column('filename'),
        Column('size', type='int'),
        Column('time', type='int'),
        Column('description'),
        Column('author'),
        Column('ipnr')],

    # Wiki system
    Table('wiki', key=('name', 'version'))[
        Column('name'),
        Column('version', type='int'),
        Column('time', type='int'),
        Column('author'),
        Column('ipnr'),
        Column('text'),
        Column('comment'),
        Column('readonly', type='int'),
        Index(['time'])],

    # Version control cache
    Table('revision', key='rev')[
        Column('rev'),
        Column('time', type='int'),
        Column('author'),
        Column('message'),
        Index(['time'])],
    Table('node_change', key=('rev', 'path', 'change_type'))[
        Column('rev'),
        Column('path'),
        Column('node_type', size=1),
        Column('change_type', size=1),
        Column('base_path'),
        Column('base_rev'),
        Index(['rev'])],

    # Ticket system
    Table('ticket', key='id')[
        Column('id', auto_increment=True),
        Column('type'),
        Column('time', type='int'),
        Column('changetime', type='int'),
        Column('component'),
        Column('severity'),
        Column('priority'),
        Column('owner'),
        Column('reporter'),
        Column('cc'),
        Column('version'),
        Column('milestone'),
        Column('status'),
        Column('resolution'),
        Column('summary'),
        Column('description'),
        Column('keywords'),
        Index(['time']),
        Index(['status'])],    
    Table('ticket_change', key=('ticket', 'time', 'field'))[
        Column('ticket', type='int'),
        Column('time', type='int'),
        Column('author'),
        Column('field'),
        Column('oldvalue'),
        Column('newvalue'),
        Index(['ticket']),
        Index(['time'])],
    Table('ticket_custom', key=('ticket', 'name'))[
        Column('ticket', type='int'),
        Column('name'),
        Column('value')],
    Table('enum', key=('type', 'name'))[
        Column('type'),
        Column('name'),
        Column('value')],
    Table('component', key='name')[
        Column('name'),
        Column('owner'),
        Column('description')],
    Table('milestone', key='name')[
        Column('name'),
        Column('due', type='int'),
        Column('completed', type='int'),
        Column('description')],
    Table('version', key='name')[
        Column('name'),
        Column('time', type='int'),
        Column('description')],

    # Report system
    Table('report', key='id')[
        Column('id', auto_increment=True),
        Column('author'),
        Column('title'),
        Column('query'),
        Column('description')],
]


##
## Default Reports
##

def get_reports(db):
    owner = db.concat('owner', "' *'")
    return (
('Active Tickets',
u'''
 * 按优先级列出所有的活动传票
 * 颜色表示不同的优先级
 * 认领者认领的传票后,会有一个'*'加到的名字后面''',
"""
SELECT p.value AS __color__,
   id AS ticket, summary, component, version, milestone, t.type AS type, 
   (CASE status WHEN 'assigned' THEN %s ELSE owner END) AS owner,
   time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE status IN ('new', 'assigned', 'reopened') 
  ORDER BY p.value, milestone, t.type, time
""" % owner),
#----------------------------------------------------------------------------
 ('Active Tickets by Version',
u'''
本报表按版本分组,和按优先级列出不同颜色的结果.

当使用RSS阅读时,最后修改时间,描述与及创建人是被隐藏的''',
"""
SELECT p.value AS __color__,
   version AS __group__,
   id AS ticket, summary, component, version, t.type AS type, 
   (CASE status WHEN 'assigned' THEN %s ELSE owner END) AS owner,
   time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE status IN ('new', 'assigned', 'reopened') 
  ORDER BY (version IS NULL),version, p.value, t.type, time
""" % owner),
#----------------------------------------------------------------------------
('Active Tickets by Milestone',
u'''
本报表按里程碑分组,和按优先级列出不同颜色的结果.

当使用RSS阅读时,最后修改时间,描述与及创建人是被隐藏的''',
"""
SELECT p.value AS __color__,
   %s AS __group__,
   id AS ticket, summary, component, version, t.type AS type, 
   (CASE status WHEN 'assigned' THEN %s ELSE owner END) AS owner,
   time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE status IN ('new', 'assigned', 'reopened') 
  ORDER BY (milestone IS NULL),milestone, p.value, t.type, time
""" % (db.concat('milestone', "' Release'"), owner)),
#----------------------------------------------------------------------------
('Assigned, Active Tickets by Owner',
u'''
按传票认领者分组,按优先级排列''',
"""

SELECT p.value AS __color__,
   owner AS __group__,
   id AS ticket, summary, component, milestone, t.type AS type, time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE status = 'assigned'
  ORDER BY owner, p.value, t.type, time
"""),
#----------------------------------------------------------------------------
('Assigned, Active Tickets by Owner (Full Description)',
u'''
按创建者分组,列出已分配的活动传票,此报表使用全描述''',
"""
SELECT p.value AS __color__,
   owner AS __group__,
   id AS ticket, summary, component, milestone, t.type AS type, time AS created,
   description AS _description_,
   changetime AS _changetime, reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE status = 'assigned'
  ORDER BY owner, p.value, t.type, time
"""),
#----------------------------------------------------------------------------
('All Tickets By Milestone  (Including closed)',
u'''
复杂的查询例子,用于展示高级查询''',
"""
SELECT p.value AS __color__,
   t.milestone AS __group__,
   (CASE status 
      WHEN 'closed' THEN 'color: #777; background: #ddd; border-color: #ccc;'
      ELSE 
        (CASE owner WHEN $USER THEN 'font-weight: bold' END)
    END) AS __style__,
   id AS ticket, summary, component, status, 
   resolution,version, t.type AS type, priority, owner,
   changetime AS modified,
   time AS _time,reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  ORDER BY (milestone IS NULL), milestone DESC, (status = 'closed'), 
        (CASE status WHEN 'closed' THEN modified ELSE (-1)*p.value END) DESC
"""),
#----------------------------------------------------------------------------
('My Tickets',
u'''
该报告展示了如何使用自动设置用户动态变量，将其替换为登录用户的用户名的方法。''',
"""
SELECT p.value AS __color__,
   (CASE status WHEN 'assigned' THEN 'Assigned' ELSE 'Owned' END) AS __group__,
   id AS ticket, summary, component, version, milestone,
   t.type AS type, priority, time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE t.status IN ('new', 'assigned', 'reopened') AND owner = $USER
  ORDER BY (status = 'assigned') DESC, p.value, milestone, t.type, time
"""),
#----------------------------------------------------------------------------
('Active Tickets, Mine first',
u'''
 * 根据优先级别列举所有传票。
 * 先显示组内登录用户的所有传票。''',
"""
SELECT p.value AS __color__,
   (CASE owner 
     WHEN $USER THEN 'My Tickets' 
     ELSE 'Active Tickets' 
    END) AS __group__,
   id AS ticket, summary, component, version, milestone, t.type AS type, 
   (CASE status WHEN 'assigned' THEN %s ELSE owner END) AS owner,
   time AS created,
   changetime AS _changetime, description AS _description,
   reporter AS _reporter
  FROM ticket t
  LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority'
  WHERE status IN ('new', 'assigned', 'reopened') 
  ORDER BY (owner = $USER) DESC, p.value, milestone, t.type, time
""" % owner))


##
## Default database values
##

# (table, (column1, column2), ((row1col1, row1col2), (row2col1, row2col2)))
def get_data(db):
   return (('component',
             ('name', 'owner'),
               (('component1', 'somebody'),
                ('component2', 'somebody'))),
           ('milestone',
             ('name', 'due', 'completed'),
               (('milestone1', 0, 0),
                ('milestone2', 0, 0),
                ('milestone3', 0, 0),
                ('milestone4', 0, 0))),
           ('version',
             ('name', 'time'),
               (('1.0', 0),
                ('2.0', 0))),
           ('enum',
             ('type', 'name', 'value'),
               (('status', 'new', 1),
                ('status', 'assigned', 2),
                ('status', 'reopened', 3),
                ('status', 'closed', 4),
                ('resolution', 'fixed', 1),
                ('resolution', 'invalid', 2),
                ('resolution', 'wontfix', 3),
                ('resolution', 'duplicate', 4),
                ('resolution', 'worksforme', 5),
                ('priority', 'blocker', 1),
                ('priority', 'critical', 2),
                ('priority', 'major', 3),
                ('priority', 'minor', 4),
                ('priority', 'trivial', 5),
                ('ticket_type', 'defect', 1),
                ('ticket_type', 'enhancement', 2),
                ('ticket_type', 'task', 3))),
           ('permission',
             ('username', 'action'),
               (('anonymous', 'LOG_VIEW'),
                ('anonymous', 'FILE_VIEW'),
                ('anonymous', 'WIKI_VIEW'),
                ('anonymous', 'WIKI_CREATE'),
                ('anonymous', 'WIKI_MODIFY'),
                ('anonymous', 'SEARCH_VIEW'),
                ('anonymous', 'REPORT_VIEW'),
                ('anonymous', 'REPORT_SQL_VIEW'),
                ('anonymous', 'TICKET_VIEW'),
                ('anonymous', 'TICKET_CREATE'),
                ('anonymous', 'TICKET_MODIFY'),
                ('anonymous', 'BROWSER_VIEW'),
                ('anonymous', 'TIMELINE_VIEW'),
                ('anonymous', 'CHANGESET_VIEW'),
                ('anonymous', 'ROADMAP_VIEW'),
                ('anonymous', 'MILESTONE_VIEW'))),
           ('system',
             ('name', 'value'),
               (('database_version', str(db_version)),
                ('youngest_rev', ''))),
           ('report',
             ('author', 'title', 'query', 'description'),
               __mkreports(get_reports(db))))


default_components = ('trac.About', 'trac.attachment',
                      'trac.db.mysql_backend', 'trac.db.postgres_backend',
                      'trac.db.sqlite_backend',
                      'trac.mimeview.enscript', 'trac.mimeview.patch',
                      'trac.mimeview.php', 'trac.mimeview.rst',
                      'trac.mimeview.silvercity', 'trac.mimeview.txtl',
                      'trac.scripts.admin',
                      'trac.Search', 'trac.Settings',
                      'trac.ticket.query', 'trac.ticket.report',
                      'trac.ticket.roadmap', 'trac.ticket.web_ui',
                      'trac.Timeline',
                      'trac.versioncontrol.web_ui',
                      'trac.versioncontrol.svn_fs',
                      'trac.wiki.macros', 'trac.wiki.web_ui',
                      'trac.web.auth')

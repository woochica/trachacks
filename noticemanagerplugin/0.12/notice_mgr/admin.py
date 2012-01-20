# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2007 Carsten Tittel <carsten.tittel@fokus.fraunhofer.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Ths code in the file is based on code written by Matthew Good. Below
# is his license:
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <trac@matt-good.net> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Matthew Good
#
# Author: Carsten Tittel <carsten.tittel@fokus.fraunhofer.de>

import inspect
import sys
import os
import re

from trac.core import *
from trac.config import Option
from trac.perm import PermissionSystem
from trac.util import sorted
from trac.util.datefmt import format_datetime
from trac.web.chrome import ITemplateProvider
from trac.admin import IAdminPanelProvider

global GROUP_PREFIX
global ldap_import
try:
	import ldap
	from ldapplugin.api import LDAP_DIRECTORY_PARAMS,LdapUtil,LdapConnection,GROUP_PREFIX
	ldap_import = 1
except ImportError:
	ldap_import = 0
	GROUP_PREFIX='*'

def _getoptions(cls):
    if isinstance(cls, Component):
        cls = cls.__class__
    return [(name, value) for name, value in inspect.getmembers(cls)
            if isinstance(value, Option)]

class NoticeManagerAdminPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    def __init__(self):
	self._ldap = 0
	self._ldapcfg = {}
	self.error_message = ""
	if ldap_import == 1:	
	    for name,value in self.config.options('ldap'):
	        if name in LDAP_DIRECTORY_PARAMS:
		    self._ldapcfg[str(name)] = value

    # IAdminPageProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('general', 'General', 'notice', 'E-Mails')

    def process_admin_request(self, req, cat, page, path_info):
        assert(req.perm.has_permission('TRAC_ADMIN'))
	if page == 'notice':
	    return self._do_notice(req)

    def _get_notice_options(self):
	self.options = {
    		'use_ldap' : self.config.get('notice-manager', 'use_ldap'),
    		'use_file' :  self.config.get('notice-manager', 'use_file'),
    		'filename' : self.config.get('notice-manager', 'filename'),
		'overwrite' : self.config.get('notice-manager','overwrite')
	}

    def _set_notice_options(self,req):
    	for opt in ['use_ldap', 'use_file', 'overwrite']:
	    if (req.args.get(opt)):
		self.options[opt] = 1
	    else:
		self.options[opt] = 0
	    self.config.set('notice-manager',opt, self.options[opt])
    	if req.args.get('filename'):
	    self.options ['filename'] = req.args.get('filename')
    	else:
	    self.options['filename'] = ""
   	self.config.set('notice-manager', 'filename', self.options['filename'])
    	self.config.save()
            
    def _get_infos(self, perms):
	userinfos = {}
	groupinfos = {}
	rejectinfos = {}

	for p in perms:
		if (p[0][0] == GROUP_PREFIX):
			infos = groupinfos
		else:
			infos = userinfos
		ainfo = infos.get(p[0])
		rejectinfo = rejectinfos.get(p[0])
		if (not ainfo) and (not rejectinfo):
			infos[p[0]] = {'id': p[0], 'name' : "", 'email' : ""}
		if not rejectinfo:
			rejectinfos[p[1]] = {'name': p[1]}
			reject_info = infos.get(p[1])
			if reject_info:
				del infos[p[1]]

        for username, name, email in self.env.get_known_users():
		if (username[0] == GROUP_PREFIX):
			infos = groupinfos
		else:
			infos = userinfos
        	ainfo = infos.get(username)
                if not ainfo:
		    infos[username] = {'id': username, 'name' : "", 'email' : ""}
		    ainfo = infos.get(username)
                ainfo['name'] = name
                ainfo['email'] = email

	return [userinfos,groupinfos]

    def _ldap_open(self):
	if ldap_import == 1:
	    if not self._ldap:
	        bind = self.config.getbool('ldap','group_bind')
	        self._ldap = LdapConnection(self.env.log, bind, **self._ldapcfg)

    def _ldap_search_group(self, groupname):
	name = ""
	email = ""
        if self._ldap.group_rdn:
                groupou = "%s,%s" % (self._ldap.group_rdn, self._ldap.basedn);
        else:
                groupou = self._ldap.basedn;

	filterstr = "(&(%s=%s)(%s=%s))" % (self._ldap.mapobjectclassgroup,self._ldap.objectclassgroupvalue,
                         self._ldap.mapgidgroup,groupname.lstrip(GROUP_PREFIX))
	for attempt in range(2):
	    sr = self._ldap._search(groupou, filterstr, ['mail','name'], ldap.SCOPE_SUBTREE)
            if sr:
                for (dn, attrs) in sr:
                        if (attrs.has_key("name")):
                                name = attrs["name"][0]
                        if (attrs.has_key("mail")):
                                email = attrs["mail"][0]
                break
            if self._ldap._ds:
                break
	return [name,email]

    def _ldap_search_user(self, username):
	name = ""
	email = ""
        if self._ldap.user_rdn:
                userou = "%s,%s" % (self._ldap.user_rdn, self._ldap.basedn);
        else:
                userou = self._ldap.basedn;
	filterstr = "(&(%s=%s)(%s=%s))" % (self._ldap.mapobjectclassuser,self._ldap.objectclassuservalue,
                         self._ldap.mapuiduser,username)
	for attempt in range(2):
	    sr = self._ldap._search(userou, filterstr, ['mail','name'], ldap.SCOPE_SUBTREE)
            if sr:
                for (dn, attrs) in sr:
                        if (attrs.has_key("name")):
                                name = attrs["name"][0]
                        if (attrs.has_key("mail")):
                                email = attrs["mail"][0]
                break
            if self._ldap._ds:
                break
	return [name,email]

    def _ldap_search_members(self, name):
	users = []
        if self._ldap.group_rdn:
                groupou = "%s,%s" % (self._ldap.group_rdn, self._ldap.basedn);
        else:
                groupou = self._ldap.basedn;
	filterstr = "(&(%s=%s)(%s=%s))" % (self._ldap.mapobjectclassgroup,self._ldap.objectclassgroupvalue,
                         self._ldap.mapgidgroup,name)
	members = []
	for attempt in range(2):
	    sr = self._ldap._search(groupou, filterstr, ['member'], ldap.SCOPE_SUBTREE)
            if sr:
                for (dn, attrs) in sr:
                        if (attrs.has_key("member")):
				for member in attrs["member"]:
					members.append(member)
                break
            if self._ldap._ds:
                break
	for member in members:
	    for attempt in range(2):
                sr = self._ldap._ds.search_s(member, ldap.SCOPE_SUBTREE, 'objectclass=*', 
			[self._ldap.mapuiduser])
                if sr:
                    for (dn,attrs) in sr:
                        if (attrs.has_key(self._ldap.mapuiduser)):
				users.append(attrs[self._ldap.mapuiduser][0])
                    break
                if self._ldap._ds:
                    break
	return users

    def _fill_from_ldap(self,userinfos, groupinfos):
	self._ldap_open()
	for groupname in groupinfos:
		group = groupinfos.get(groupname)
		if ((group['name'] == "") and (group['email'] == "")) or (self.options['overwrite'] == 1):
			(name,email) = self._ldap_search_group(groupname)
			if name == "":
				name = group['name']
			if (email == ""):
				email = group['email']
			if (name != "") or (email != ""):
				self._save_user_info(groupname, name, email)
				group['name'] = name
				group['email'] = email

	for username in userinfos:
		user = userinfos.get(username)
		if ((user['name'] == "") and (user['email'] == "")) or (self.options['overwrite'] == 1):
			(name,email) = self._ldap_search_user(username)
			if name == "":
				name = user['name']
			if (email == ""):
				email = user['email']
			if (name != "") or (email != ""):
				self._save_user_info(username, name, email)
				user['name'] = name
				user['email'] = email

    def _fill_from_file(self, req, userinfos, groupinfos):
	if not req.args.get('filename'):
		self.error_message="No filename was specified. Cannot use information from a file."
		return
	filename = req.args.get('filename')
	if not os.path.exists(filename):
		self.error_message="Filenote %s not found. Cannot use information from a file." % filename
		return
	f = open(filename)
	for line in f:
	    if re.match('\s*#',line):
		continue
	    try:
	        (id,name,email) = line.split(':')
	    except ValueError:
		continue	
	    id = id.strip()
	    name = name.strip()
	    email = email.strip()
            if (id[0] == GROUP_PREFIX):
            	infos = groupinfos
            else:
            	infos = userinfos
            ainfo = infos.get(id)
            if not ainfo:
            	infos[id] = {'id': id, 'name' : name, 'email' : email}
		ainfo = infos.get(id)
	    else:
		if (ainfo['name'] == "") or ((self.options['overwrite'] == 1) and (name!='')):
			ainfo['name'] = name
		if (ainfo['email'] == "") or ((self.options['overwrite'] == 1) and (email!='')):
			ainfo['email'] = email
	    self._save_user_info(id, ainfo['name'], ainfo['email']) 
	f.close()
	return

    def _fill_from_fields(self,req,userinfos, groupinfos):
        if req.args.get('change_id'):
	    id=req.args.get('change_id')
	    if (id[0] == GROUP_PREFIX):
		infos = groupinfos
	    else:
		infos = userinfos
	    ainfo = infos.get(id)
	    if ainfo: 
		name = ainfo['name']
		email = ainfo['email']
	    else:
		infos[id] = {'id': id, 'name' : "", 'email' : ""}
		ainfo = infos.get(id)
		name = ""
		email = ""
	    change_name = req.args.get('change_name')
	    if change_name and (change_name != ""):
		name = change_name
		ainfo['name'] = change_name
	    change_mail = req.args.get('change_mail')
	    if change_mail and (change_mail != ""):
		email = change_mail
		ainfo['email'] = change_mail
	    self._save_user_info(id, name, email)

    def _save_user_info(self, username, name, email):
	db = self.env.get_db_cnx()
	arr = { 'name' : name, 'email' : email, 'email_verification_sent_to' : email}
	cursor = db.cursor()
	cursor.execute("SELECT count(*) FROM session "
                        "WHERE sid=%s AND authenticated=1",
                        (username,))
        exists, = cursor.fetchone()
        if not exists:
	    cursor.execute("INSERT INTO session "
                       "(sid, authenticated, last_visit) "
                       "VALUES (%s, 1, 0)",
                       (username,))

        for key in ('name', 'email_verification_sent_to', 'email'):
            value = arr.get(key)
            if not value:
            	continue
            cursor.execute("UPDATE session_attribute SET value=%s "
                       "WHERE name=%s AND sid=%s AND authenticated=1",
                       (value.decode('utf-8'), key.decode('utf-8'), username.decode('utf-8')))
            if not cursor.rowcount:
                cursor.execute("INSERT INTO session_attribute "
                           "(sid,authenticated,name,value) "
                           "VALUES (%s,1,%s,%s)",
                           (username.decode('utf8'), key.decode('utf-8'), 
				value.decode('utf-8')))
	db.commit()

    def _rm_user(self, req, userinfos, groupinfos):
	db = self.env.get_db_cnx()
	cursor = db.cursor()
	sel = req.args.get('sel')
        sel = isinstance(sel, list) and sel or [sel]

        for account in sel:
	    if (not account) or (account == None):
		continue
            cursor.execute("DELETE FROM session_attribute WHERE sid=%s", (account,))
            cursor.execute("DELETE FROM session WHERE sid=%s", (account,))
	    if (account[0] == GROUP_PREFIX):
		del groupinfos[account]
	    else:
		del userinfos[account]
	db.commit()

    def _rm_info(self, req, userinfos, groupinfos):
	db = self.env.get_db_cnx()
	cursor = db.cursor()
	sel = req.args.get('sel')
        sel = isinstance(sel, list) and sel or [sel]

        for account in sel:
	    if (not account) or (account == None):
		continue
            cursor.execute("DELETE FROM session_attribute WHERE sid=%s", (account,))
	    if (account[0] == GROUP_PREFIX):
		groupinfos[account] = { 'id' : account, 'name' : "", 'email' : ""}
	    else:
		userinfos[account] = { 'id' : account, 'name' : "", 'email' : ""}
	db.commit()

    def _rm_all(self, req, userinfos, groupinfos):
	db = self.env.get_db_cnx()
	cursor = db.cursor()
	
	sel = []
	for account in userinfos:
	    sel.append(account)

	for account in groupinfos:
	    sel.append(account)

        for account in sel:
            cursor.execute("DELETE FROM session_attribute WHERE sid=%s", (account,))
            cursor.execute("DELETE FROM session WHERE sid=%s", (account,))
	    if (account[0] == GROUP_PREFIX):
		del groupinfos[account]
	    else:
		del userinfos[account]
	db.commit()

    def _extract_groups(self, req, userinfos, groupinfos):
	self._ldap_open()
	sel = req.args.get('sel')
        sel = isinstance(sel, list) and sel or [sel]

        for account in sel:
	    if (not account) or (account == None):
		continue
	    if (account[0] != GROUP_PREFIX):
		continue
	    users = self._ldap_search_members(account)
	    if users:
		for user in users:
		    auser = userinfos.get(user)
		    if not auser:
		        userinfos[user] = { 'id' : user, 'name' : "", 'email' : ""}
		        self._save_user_info(user, "", "")

    def _do_notice(self, req):
        perm = PermissionSystem(self.env)
        perms = perm.get_all_permissions()

	self._get_notice_options()
	(userinfos, groupinfos) = self._get_infos(perms)
	if req.method == 'POST':
	    if req.args.get('fill'):
	        self._set_notice_options(req)
		if req.args.get('use_ldap'):
			self._fill_from_ldap(userinfos,groupinfos)
		if req.args.get('use_file'):
			self._fill_from_file(req,userinfos,groupinfos)
	    if req.args.get('change'):
		self._fill_from_fields(req,userinfos,groupinfos)
	    if req.args.get('rmuser'):
		self._rm_user(req,userinfos,groupinfos)
		(userinfos, groupinfos) = self._get_infos(perms)
	    if req.args.get('rminfo'):
		self._rm_info(req,userinfos,groupinfos)
	    if req.args.get('rmall'):
		self._rm_all(req,userinfos,groupinfos)
		(userinfos, groupinfos) = self._get_infos(perms)
		if (len(userinfos) > 0) or (len(groupinfos)>0):
		    self.error_message = "As long as permissions are defined for users/group, " + \
			"they cannot be delete from this list."
	    if req.args.get('extract'):
		self._extract_groups(req,userinfos,groupinfos)

	# need a new index for clearsilver to understand names including '.'
	newuserinfos = {}
	cnt=0
	for ui in userinfos:
                auser = userinfos.get(ui)
		newuserinfos[cnt] = auser
		cnt+=1
	req.hdf['admin.userinfos'] = newuserinfos
	req.hdf['admin.groupinfos'] = groupinfos
	req.hdf['admin.ldap_import'] = ldap_import
	req.hdf['admin.options'] = self.options
	if self.error_message:
        	req.hdf['admin.error_message'] = self.error_message
	return 'admin_notice.cs', None

    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2005 Jani Tiainen
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# NlWikinfo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Jani Tiainen <redetin@luukku.com>

from __future__ import generators
import imp
import inspect
import os.path
import time
import shutil
import re

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

class WikinfoMacro(Component):
	"""
	Output different information by keyword.
	
	Currently supported infos:
	
	author	      - Author of first version
	version       - Latest version of page
	changed_by    - Page last changed by
	comment       - Latest comment of changed by
	changed_ts    - Page last changed timestamp
	"""
	implements(IWikiMacroProvider)
	
	# IWikiMacroProvider methods
	def get_macros(self):
		yield 'Wikinfo'
	
	def get_macro_description(self, name):
		return inspect.getdoc(WikinfoMacro)
	
	def render_macro(self, req, name, content):
		if content:
			keywords = [arg.strip() for arg in content.split(',')]
		
		buf = StringIO()
		
		for nfo in keywords:
			try:
				getattr(self, '_do_%s' % nfo)(req, name, content, buf)
			except AttributeError:
				buf.write('INVALID: %s' % nfo)
			
		return buf.getvalue()

	# Private methods
	def _do_author(self, req, name, content, buf):
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		sql = "SELECT author, version FROM wiki where name = '%s' order by version limit 1" % req.hdf['wiki.page_name']
		cursor.execute(sql)
		
		row = cursor.fetchone()
		
		buf.write(row[0])
		
	def _do_version(self, req, name, content, buf):
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		sql = "SELECT max(version) FROM wiki where name = '%s'" % req.hdf['wiki.page_name']
		cursor.execute(sql)
		
		row = cursor.fetchone()
		
		buf.write(str(row[0]))

	def _do_changed_by(self, req, name, content, buf):
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		sql = "SELECT author, version FROM wiki where name = '%s' order by version desc limit 1" % req.hdf['wiki.page_name']
		cursor.execute(sql)
		
		row = cursor.fetchone()
		
		buf.write(row[0])

	def _do_changed_ts(self, req, name, content, buf):
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		sql = "SELECT time, version FROM wiki where name = '%s' order by version desc limit 1" % req.hdf['wiki.page_name']
		cursor.execute(sql)
		
		row = cursor.fetchone()
		
		buf.write(time.strftime('%x', time.localtime(row[0])))

	def _do_comment(self, req, name, content, buf):
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		sql = "SELECT comment, version FROM wiki where name = '%s' order by version desc limit 1" % req.hdf['wiki.page_name']
		cursor.execute(sql)
		
		row = cursor.fetchone()
		
		buf.write(row[0])


#!/usr/bin/python

#
# created by Marcelo Salhab Brogliato
# last update at January, 16, 2008
# email: msbrogli at gmail dot com
#
# any bug correction, new feature or suggestion are welcome
#
#

import sys
import google
import os
import string
import config
from pysqlite2 import dbapi2 as sqlite
from string import Template as Template

class HTMLTemplate:
	def __init__(self, title):
		self.tpl_index = self.readTemplate('template_index.tpl')
		self.tpl_report = self.readTemplate('template_report.tpl')
		self.tpl_details = self.readTemplate('template_details.tpl')
		self.index_body = ''
		self.title = title
	def readTemplate(self, filename):
		fp = open(filename, 'r')
		str = fp.read()
		fp.close()
		return str
	def openReport(self, title, description):
		self.report_title = title
		self.report_description = description
		self.report_details = ''
	def closeReport(self):
		t = Template(self.tpl_report)
		self.index_body += t.substitute(title=self.report_title, description=self.report_description,
			details=self.report_details)
	def addDetails(self, filename, data):
		t = Template(self.tpl_details)
		self.report_details += t.substitute(img=filename, data=data)
	def write(self, filename):
		t = Template(self.tpl_index)
		contents = t.substitute(title=self.title, body=self.index_body)
		fp = open(filename, 'w')
		fp.write(contents)
		fp.close()


for arg in sys.argv[1:]:
	print arg

#PROJ = 'blueocean'
PROJ = config.project
DBFILE = '/srv/trac/%s/db/trac.db' % PROJ
REPORTDIR = '%s_reports' % PROJ

print 'opening database'
if (os.path.isfile(DBFILE) == 0):
	print 'error: database not found'
	sys.exit(1)
con = sqlite.connect(DBFILE)
cur = con.cursor()

if (os.path.isdir(REPORTDIR) == False):
	print 'creating report directory'
	os.mkdir(REPORTDIR)

template = HTMLTemplate(config.title)

for report in config.reports:
	print 'generating %s report' % report['title']
	template.openReport(report['title'], report.get('description', ''))
	if (report.get('sql', None) is None):
		for query in report['queries']:
			cur.execute(query['sql'])
			res = cur.fetchall()
			if (len(res) == 0):
				print '  ignoring %s graph' % query['title']
				continue
			if (len(res[0]) == 1):
				labels = query['labels']
				data = [ i[0] for i in res ]
			elif (len(res[0]) == 2):
				labels = [ i[0] for i in res ]
				data = [ i[1] for i in res ]
			print '  generating %s graph' % query['title']
			saveas = '%s/%s' % (REPORTDIR, query['filename'])
			google.graph(query['type'], data, labels, title=query['title'], filename=saveas)
			template.addDetails(query['filename'], '')
	else:
		entries = cur.execute(report['sql'])
		for entry in entries.fetchall():
			for query in report['queries']:
				t = Template(query['sql'])
				sql = t.substitute(item=entry[0])
				t = Template(query['title'])
				title = t.substitute(item=entry[0])
				cur.execute(sql)
				res = cur.fetchall()
				if (len(res) == 0):
					print '  ignoring %s graph' % query['title']
					continue
				if (len(res[0]) == 1):
					labels = query['labels']
					data = [ i[0] for i in res ]
				elif (len(res[0]) == 2):
					labels = [ i[0] for i in res ]
					data = [ i[1] for i in res ]
				print '  generating %s graph' % title
				saveas = '%s/%s_%s' % (REPORTDIR, entry[0], query['filename'])
				google.graph(query['type'], data, labels, title=title, filename=saveas)
				template.addDetails(entry[0] + '_' + query['filename'], '')
		
	template.closeReport()

template.write('%s/%s' % (REPORTDIR, 'index.html'))


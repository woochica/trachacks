import os
from trac import perm, util, db_default
from trac.env import Environment
from trac.wiki.api import WikiSystem
from trac.wiki import WikiPage
from trac.attachment import Attachment

class Trac(object):
	def __init__(self, path):
		'''Basic object that supports the wiki and all that jazz'''
		self._env = Environment(os.path.abspath(path))
		purl = self._env.project_url
		if purl.endswith('/'):
			purl = purl[:-1]
		if purl:
			self.name = purl.split('/')[-1]
		else:
			self.name = self._env.project_name

	def listWikiPages(self):
		'''Return a list of all wiki pages that were not written by the 'trac' user'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		wikiPagesQuery = "select distinct name from wiki where author != 'trac'"
		res = cursor.execute(wikiPagesQuery)
		pages = res.fetchall()
		names = [x[0] for x in pages]
		return names

	def listTickets(self):
		'''Return a list of all ticket numbers'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		ticketsQuery = 'select distinct id from ticket'
		res = cursor.execute(ticketsQuery)
		ticketsRes = res.fetchall()
		tickets = [x[0] for x in ticketsRes]
		return tickets
		
	def maxTicket(self):
		'''Return the largest ticket number'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		maxTicketQuery = 'select max(id) from ticket'
		res = cursor.execute(maxTicketQuery)
		(maxTicket, ) = res.fetchone()
		return maxTicket
		
	def listVersions(self):
		'''List all the versions'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		versionsQuery = "select name from version"
		res = cursor.execute(versionsQuery)
		versions = [x[0] for x in res.fetchall()]
		return versions

	def listComponents(self):
		'''List all the ticket components'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		componentsQuery = "select name from component"
		res = cursor.execute(componentsQuery)
		components = [x[0] for x in res.fetchall()]
		return components

	def listEnums(self):
		'''List all the enums'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		enumsQuery = "select name, type from enum"
		res = cursor.execute(enumsQuery)
		return res.fetchall()

	def listMilestones(self):
		'''List all the milestones'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		milestonesQuery = "select name from milestone"
		res = cursor.execute(milestonesQuery)
		milestones = [x[0] for x in res.fetchall()]
		return milestones

	def getAllInfo(self):
		all = {}
		all['wikiNames'] = self.listWikiPages()
		all['maxTicket'] = self.maxTicket()
		all['versions'] = self.listVersions()
		all['components'] = self.listComponents()
		all['enums'] = self.listEnums()
		all['milestones'] = self.listMilestones()
		return all
	
	def getWikiPageAll(self, page):
		'''Get all the versions of a wiki page as a list of dicts and a list of attachments'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		pageCountRes = cursor.execute('select count(*) as count from wiki where name = %s', (page,))
		pageCount = pageCountRes.fetchone()[0]
		assert pageCount >= 1, 'Page %s not found in %s' % (page, self.name)

		attachments = []
		pageAttachmentQuery = "select type, id, filename, size, time, description, author, ipnr from attachment where type = 'wiki' and id = %s"
		pageAttachmentRes = cursor.execute(pageAttachmentQuery, (page,))
		for attachment in pageAttachmentRes:
			thisAttachment = dict(zip([d[0] for d in pageAttachmentRes.description], attachment))
			thisAttachment['fileobj'] = Attachment(self._env, 'wiki', page, thisAttachment['filename']).open()
			attachments.append(thisAttachment)

		baseQuery = 'select name, version, time, author, ipnr, text, comment, readonly from wiki where name = %s'
		res = cursor.execute(baseQuery, (page,))
		wikiData = []
		for row in res:
			wikiData.append(dict(zip([d[0] for d in res.description], row)))
		return wikiData, attachments

	def getWikiPageCurrent(self, page):
		'''Get the current version of a wiki page as a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		pageCountRes = cursor.execute('select count(*) as count from wiki where name = %s', (page,))
		pageCount = pageCountRes.fetchone()[0]
		assert pageCount >= 1, 'Page %s not found in %s' % (page, self.name)
		pageQuery = 'select name, version, time, author, ipnr, text, comment, readonly from wiki where name = %s and version = (select max(version) from wiki where name = %s)'
		pageRes = cursor.execute(pageQuery, (page,page))
		wikiPage = dict(zip([d[0] for d in pageRes.description], pageRes.fetchone()))

		wikiPage['attachment'] = []
		pageAttachmentQuery = "select type, id, filename, size, time, description, author, ipnr from attachment where type = 'wiki' and id = %s"
		pageAttachmentRes = cursor.execute(pageAttachmentQuery, (page,))
		for attachment in pageAttachmentRes:
			thisAttachment = dict(zip([d[0] for d in pageAttachmentRes.description], attachment))
			thisAttachment['fileobj'] = Attachment(self._env, 'wiki', page, thisAttachment['filename']).open()
			wikiPage['attachment'].append(thisAttachment)
		return wikiPage

	def addWikiPage(self, page, attachments):
		'''Add a wiki page as a list of dictionaries'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		pageCountRes = cursor.execute('select count(*) as count from wiki where name = %s', (page[0]['name'],))
		pageCount = pageCountRes.fetchone()[0]
		assert pageCount == 0, 'Page %s found in %s' % (page[0]['name'], self.name)

		insertWikiQuery = 'insert into wiki (name, version, time, author, ipnr, text, comment, readonly) values (%s, %s, %s, %s, %s, %s, %s, %s)'
		for pV in page:
			insertValues = (pV['name'], pV['version'], pV['time'], pV['author'], pV['ipnr'], pV['text'], pV['comment'], pV['readonly'])
			insertRes = cursor.execute(insertWikiQuery, insertValues)
		for a in attachments:
			pageAttach = Attachment(self._env, 'wiki', pV['name'])
			pageAttach.description = a['description']
			pageAttach.author = a['author']
			pageAttach.ipnr = a['ipnr']
			pageAttach.insert(a['filename'], a['fileobj'], a['size'], t=a['time'])
		db.commit()
		

	def getTicket(self, id):
		'''Get a ticket id as a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		idCountRes = cursor.execute('select count(*) as count from ticket where id = %s', (id,))
		idCount = idCountRes.fetchone()[0]
		assert idCount >= 1, 'Page %s not found in %s' % (id, self.id)

		mainTicketQuery = 'select id, type, time, changetime, component, severity, priority, owner, \
			reporter, cc, version, milestone, status, resolution, summary, description, keywords from ticket where id = %s'
		mainTicketRes = cursor.execute(mainTicketQuery, (id, ))
		ticket = dict(zip([d[0] for d in mainTicketRes.description], mainTicketRes.fetchone()))

		ticket['ticket_change'] = []
		ticketChangeQuery = 'select time, author, field, oldvalue, newvalue from ticket_change where ticket = %s'
		ticketChangeRes = cursor.execute(ticketChangeQuery, (id, ))
		for ticket_change in ticketChangeRes:
			ticket['ticket_change'].append(dict(zip([d[0] for d in ticketChangeRes.description], ticket_change)))

		ticket['attachment'] = []
		ticketAttachmentQuery = 'select type, id, filename, size, time, description, author, ipnr from attachment where type = \'ticket\' and id = %s'
		ticketAttachmentRes = cursor.execute(ticketAttachmentQuery, (id, ))
		for attachment in ticketAttachmentRes:
			thisAttachment = dict(zip([d[0] for d in ticketAttachmentRes.description], attachment))
			thisAttachment['fileobj'] = Attachment(self._env, 'ticket', id, thisAttachment['filename']).open()
			ticket['attachment'].append(thisAttachment)
		return ticket
		
	def addTicket(self, ticket, source):
		'''Add a ticket from a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		idCountRes = cursor.execute('select count(*) as count from ticket where id = %s', (ticket['id'],))
		idCount = idCountRes.fetchone()[0]
		assert idCount == 0, 'Ticket %s found in %s' % (ticket['id'], self.name)

		insertMainTicketQuery = 'insert into ticket (id, type, time, changetime, component, severity, priority, owner, \
			reporter, cc, version, milestone, status, resolution, summary, description, keywords) \
			values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
		insertMainTicketValues = (ticket['id'], ticket['type'], ticket['time'], ticket['changetime'], ticket['component'], \
			ticket['severity'], ticket['priority'], ticket['owner'], ticket['reporter'], ticket['cc'], ticket['version'], \
			ticket['milestone'], ticket['status'], ticket['resolution'], ticket['summary'], ticket['description'], ticket['keywords'])
		insertMainTicketRes = cursor.execute(insertMainTicketQuery, insertMainTicketValues)

		#so we know where the ticket came from
		insertTicketSourceQuery = 'insert into ticket_custom (ticket, name, value) values (%s, %s, %s)'
		insertTicketSourceValues = (ticket['id'], 'project', source)
		insertTicketSourceRes = cursor.execute(insertTicketSourceQuery, insertTicketSourceValues)

		insertTicketChangeQuery = 'insert into ticket_change (ticket, time, author, field, oldvalue, newvalue) values (%s, %s, %s, %s, %s, %s)'
		for ticket_change in ticket['ticket_change']:
			insertTicketChangeValues = (ticket['id'], ticket_change['time'], ticket_change['author'], ticket_change['field'], ticket_change['oldvalue'], ticket_change['newvalue'])
			insertTicketChangeRes = cursor.execute(insertTicketChangeQuery, insertTicketChangeValues)

		for a in ticket['attachment']:
			ticketAttach = Attachment(self._env, 'ticket', ticket['id'])
			ticketAttach.description = a['description']
			ticketAttach.author = a['author']
			ticketAttach.ipnr = a['ipnr']
			ticketAttach.insert(a['filename'], a['fileobj'], a['size'], t=a['time'])
		db.commit()
		
	def getComponent(self, comp):
		'''Get a component as a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		compCountRes = cursor.execute('select count(*) as count from component where name = %s', (comp,))
		compCount = compCountRes.fetchone()[0]
		assert compCount >= 1, 'Component %s not found in %s' % (comp, self.name)
		baseQuery = 'select name, owner, description from component where name = %s'
		res = cursor.execute(baseQuery, (comp,))
		return(dict(zip([d[0] for d in res.description], res.fetchone())))

	def addComponent(self, comp):
		'''Add a component from a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		assert comp['name'] != '', 'No name given' 
		compCountRes = cursor.execute('select count(*) as count from component where name = %s', (comp['name'],))
		compCount = compCountRes.fetchone()[0]
		if compCount > 0:
			'Component %s found in %s. Skipping the re-insertion.' % (comp['name'], self.name)
		else:
			insertComponentQuery = 'insert into component (name, owner, description) values (%s, %s, %s)'
			insertComponentValues = (comp['name'], comp['owner'], comp['description'])
			res = cursor.execute(insertComponentQuery, insertComponentValues)
			db.commit()

	def getMilestone(self, mile):
		'''Get a milestone as a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		mileCountRes = cursor.execute('select count(*) as count from milestone where name = %s', (mile,))
		mileCount = mileCountRes.fetchone()[0]
		assert mileCount >= 1, 'Milestone %s not found in %s' % (mile, self.name)

		baseQuery = 'select name, due, completed, description from milestone where name = %s'
		res = cursor.execute(baseQuery, (mile,))
		return(dict(zip([d[0] for d in res.description], res.fetchone())))

	def addMilestone(self, mile):
		'''Add a milestone from a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		assert mile['name'] != '', 'No name given' 
		mileCountRes = cursor.execute('select count(*) as count from milestone where name = %s', (mile['name'],))
		mileCount = mileCountRes.fetchone()[0]
		if mileCount > 0:
			'Milestone %s found in %s. Skipping the re-insertion.' % (mile['name'], self.name)
		else:
			insertMilestoneQuery = 'insert into milestone (name, due, completed, description) values (%s, %s, %s, %s)'
			insertMilestoneValues = (mile['name'], mile['due'], mile['completed'], mile['description'])
			res = cursor.execute(insertMilestoneQuery, insertMilestoneValues)
			db.commit()

	def getEnum(self, enum):
		'''Get an enum as a dict. Enum should be a tupe of (name, type)'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		enumCountRes = cursor.execute('select count(*) as count from enum where name = %s and type = %s', enum)
		enumCount = enumCountRes.fetchone()[0]
		assert enumCount >= 1, 'Enum %s not found in %s' % (enum, self.name)

		baseQuery = 'select name, type, value from enum where name = %s and type = %s'
		res = cursor.execute(baseQuery, enum)
		return(dict(zip([d[0] for d in res.description], res.fetchone())))

	def addEnum(self, enum):
		'''Add a enum from a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		assert enum['name'] != '', 'No name given' 
		enumCountRes = cursor.execute('select count(*) as count from enum where name = %s and type = %s', (enum['name'], enum['type']))
		enumCount = enumCountRes.fetchone()[0]
		if enumCount > 0:
			print 'Enum %s found in %s. Skipping the re-insertion.' % (enum['name'], self.name)
		else:
			insertEnumQuery = 'insert into enum (name, type, value) values (%s, %s, %s)'
			insertEnumValues = (enum['name'], enum['type'], enum['value'])
			res = cursor.execute(insertEnumQuery, insertEnumValues)
			db.commit()

	def getVersion(self, version):
		'''Get a version as a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		versionCountRes = cursor.execute('select count(*) as count from version where name = %s', (version,))
		versionCount = versionCountRes.fetchone()[0]
		assert versionCount >= 1, 'Version %s not found in %s' % (version, self.name)

		baseQuery = 'select name, time, description from version where name = %s'
		res = cursor.execute(baseQuery, (version,))
		return(dict(zip([d[0] for d in res.description], res.fetchone())))

	def addVersion(self, version):
		'''Add a version from a dict'''
		db = self._env.get_db_cnx()
		cursor = db.cursor()
		assert version['name'] != '', 'No name given' 
		versionCountRes = cursor.execute('select count(*) as count from version where name = %', (version['name'],))
		versionCount = versionCountRes.fetchone()[0]
		if versionCount > 0:
			print 'Version %s found in %s. Skipping the re-insertion.' % (version['name'], self.name)
		else:
			insertVersionQuery = 'insert into version (name, time, description) values (%s, %s, %s)'
			insertVersionValues = (version['name'], version['time'], version['description'])
			res = cursor.execute(insertVersionQuery, insertVersionValues)
			db.commit()


	def getRepository(self):
		'''Get the repository info, particularly the path and type'''
		repository = {}
		repository['type'] = self._env.config.get('trac', 'repository_type')
		repository['dir'] = self._env.config.get('trac', 'repository_dir')
		return repository

	def addRepository(self, repository):
		'''Add a repository from a dict specifying name, type and dir.
		This adds using the multiple repository functionality.'''
		assert repository.has_key('name') and repository.has_key('type') and repository.has_key('dir'), "Repository info not specified"
		self._env.config.set('repositories', '%s.dir' % repository['name'], repository['dir'])
		if repository['type'] == 'svn':
			repotype = 'direct-svnfs'
		else:
			repotype = repository['type']
		self._env.config.set('repositories', '%s.type' % repository['name'], repotype)
		self._env.config.save()

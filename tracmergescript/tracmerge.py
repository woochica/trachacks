import os
import time
from ptrac import *
from trac.admin.console import TracAdmin
import re

ticketRe = re.compile(r'(\[?(?:ticket:|#))(\d{1,3})(?:\b|$)')
genericRevRe1 = re.compile(r'(\br|\[|changeset:)(\d{1,4})(?:]|$|[,.]|(?=\s))')
genericRevRe2 = re.compile(r'(\br|\[|changeset:)(\d{1,4})[-:](\d{1,4})(?:]|$|[,.]|(?=\s))')
genericRevRe3 = re.compile(r'@(\d{1,4})(?:]|$|[,.]|(?=\s))')


class MergeTracs(object):
	"""Merges N source tracs to M destination tracs, updating text as defined."""

	def __init__(self, mergeConfig, sources, dests):
		self.config = mergeConfig
		try:
			self.user_map = mergeConfig['user_map']
		except KeyError:
			self.user_map = {}
		self.sources = sources
		self.dests = dests
		for key in self.sources.keys():
			t = self.sources[key]
			self.sources[key]['name'] = key
			self.sources[key]['trac'] = Trac(t['path'])

	def initDestinations(self):
		"""Runs the trac initialization script for each destination trac and applies and config values"""
		for dest_name in self.dests.keys():
			inheritFile = [x[2] for x in self.dests[dest_name]['configs'] if x[0] == 'inherit' and x[1] == 'file']
			if inheritFile:
				inheritOpt = '--inherit=/var/trac/common/conf/trac.ini'
			else:
				inheritOpt = ''
			initline = "'%s' '%s' '%s' '%s' %s" % (dest_name, \
				self.dests[dest_name]['db'], self.dests[dest_name]['repo_type'], self.dests[dest_name]['repo_dir'], inheritOpt)
			destination = os.path.abspath(self.dests[dest_name]['path'])
			destAdmin = TracAdmin(destination)
			destAdmin.do_initenv(initline)
			self.dests[dest_name]['trac'] = Trac(destination)
			if self.dests[dest_name]['repo_type'] == 'hg':
				self.dests[dest_name]['trac']._env.config.set('components', 'tracext.hg.*', 'enabled')
			if self.dests[dest_name].has_key('configs'): 
				for confSection, confName, confValue in self.dests[dest_name]['configs']:
					self.dests[dest_name]['trac']._env.config.set(confSection, confName, confValue)
			self.dests[dest_name]['trac']._env.config.save()

	def _updateAuthor(self, author):
		"""Return the new name of an author based on the config."""
		if self.user_map.has_key(author):
			newAuthor = self.user_map[author]
		else:
			newAuthor = author
		return newAuthor

	def _updateText(self, sTrac, oldText, myDest=''):
		"""Update the traclinks in a string, returning the modified, or orig if there were no changes, string."""
		newText = oldText
		defaultDest = self.sources[sTrac]['default_dest']
		myDest = myDest or defaultDest

		#ticket Renames
		ticketPad = int(self.sources[sTrac]['ticket_pad'])
		newText = ticketRe.sub(lambda x: x.group(1) + str(int(x.group(2))+ticketPad), newText)
		
		#Repository
		for sT in self.sources.keys():
			if self.sources[sT].has_key('revmap') and not self.sources[sT].has_key('RREs'):
				self.sources[sT]['RREs'] = []
				for oldRev, newRev in self.sources[sT]['revmap']:
					self.sources[sT]['RREs'].append((re.compile(r"(\br|\[|changeset:)(%s)(?:]|$|[\s,.])" % re.escape(oldRev)),
						'[%s/%s]' % (newRev, sT.lower())))
					self.sources[sT]['RREs'].append((re.compile(r"@(%s)(?:]|$|[,.\s])" % re.escape(oldRev)),
						'@%s/%s' % (newRev, sT.lower())))

		if myDest == defaultDest:
			if self.sources[sTrac].has_key('revmap'):
				for rev in self.sources[sTrac]['RREs']:
					newText = rev[0].sub(rev[1], newText)
			else:
				newText = genericRevRe1.sub(lambda x: '[%s/%s]' % (x.group(2), sTrac.lower()), newText)
				newText = genericRevRe2.sub(lambda x: '[%s:%s/%s]' % (x.group(2), x.group(3), sTrac.lower()), newText)
				newText = genericRevRe3.sub(lambda x: '@%s/%s' % (x.group(1), sTrac.lower()), newText)
		
		#Wiki Renames
		for sT in self.sources.keys():
			if not self.sources[sT].has_key('WREs'):
				self.sources[sT]['WREs'] = []
				for pageOldName, (pageDest, pageNewName) in self.sources[sT]['wikimap'].items():
					if pageDest == '' or pageNewName == '':
						continue
					self.sources[sT]['WREs'].append((re.compile(r"(?:^|\b)(?<!!)(\[)?(wiki:)?(')?(%s)(')?(?:\b|$)" 
						% re.escape(pageOldName)), pageDest, pageNewName))
		for pageRe, pageDest, pageNewName in self.sources[sTrac]['WREs']:
			if myDest == pageDest:
				newText = pageRe.sub(lambda x: (x.group(1) or '') + (x.group(2) or '') + (x.group(3) or '') + pageNewName + (x.group(5) or ''), newText)
			else:
				newText = pageRe.sub(lambda x: (x.group(1) or '') + pageDest.lower() + ':wiki:' + pageNewName, newText)
		return newText
		

	def merge(self):
		'''Perform all the merges needed'''
		self.mergeWiki()
		self.mergeMilestone()
		self.mergeEnum()
		self.mergeComponent()
		self.mergeTicket()
		self.mergeRepository()

	def mergeWiki(self):
		'''Merge the wikis.'''
		collisions = checkCollisions(*[x['trac'] for x in self.sources.values()])
		wikiCollisions = [x[0] for x in collisions['wiki']]
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			wikiMap = sTrac['wikimap']
			for oldPageName in sorted(sTrac['trac'].listWikiPages()):
				updateName = False
				if wikiMap.has_key(oldPageName):
					if wikiMap[oldPageName] == ('',''):
						#These are things we want to drop
						print "Dropping %s:%s because it's set to double blank" % (sTrac['name'], oldPageName)
						continue
					if wikiMap[oldPageName][1] != '':
						#We have a good destination and name. Let's set them
						pageDest, newPageName = wikiMap[oldPageName]
						if oldPageName != newPageName:
							updateName = True
					else:
						#Destination name is blank. That's the same as a default map. 
						pageDest = wikiMap[oldPageName][0]
				else:
					#Using existing name with the default destination
					pageDest = dest
				pageData, attachmentData = sTrac['trac'].getWikiPageAll(oldPageName)
				if updateName:
					for version in pageData:
						version['name'] = newPageName
					for attachment in attachmentData:
						attachment['id'] = newPageName
					newPageEntry = pageData[-1].copy()
					newPageEntry['author'] = 'tracmerge'
					newPageEntry['ipnr'] = '127.0.0.1'
					newPageEntry['comment'] = 'Tracmerge changed name from %s to %s' % (oldPageName, newPageName)
					newPageEntry['time'] = time.time()
					newPageEntry['version'] += 1
					pageData.append(newPageEntry)
					print 'Page %s:%s is now %s:%s' % (sTrac['name'], oldPageName, pageDest, pageData[-1]['name'])
				newText = self._updateText(sTrac['name'], pageData[-1]['text'], pageDest)
				if newText != pageData[-1]['text']:
					if updateName:
						newPageEntry['text'] = newText
						newPageEntry['comment'] += '. Links updated'
						pageData[-1] = newPageEntry
					else:
						newPageEntry = pageData[-1].copy()
						newPageEntry['text'] = newText
						newPageEntry['author'] = 'tracmerge'
						newPageEntry['ipnr'] = '127.0.0.1'
						newPageEntry['comment'] = 'Links updated'
						newPageEntry['time'] = time.time()
						newPageEntry['version'] += 1
						pageData.append(newPageEntry)
					print 'Links updated for %s:%s' % (sTrac['name'], oldPageName)
				for version in pageData:
					version['author'] = self._updateAuthor(version['author'])
				for attachment in attachmentData:
					attachment['author'] = self._updateAuthor(attachment['author'])
				self.dests[pageDest]['trac'].addWikiPage(pageData, attachmentData)
		
	def mergeMilestone(self):
		'''Merge the milestone components.'''
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			milestones = sTrac['trac'].listMilestones()
			for milestone in milestones:
				milestoneData = sTrac['trac'].getMilestone(milestone)
				if milestoneData['description']:
					milestoneData['description'] = self._updateText(sTrac['name'], milestoneData['description'])
				self.dests[dest]['trac'].addMilestone(milestoneData)
		
	def mergeEnum(self):
		'''Merge the enum values.'''
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			enums = sTrac['trac'].listEnums()
			for enum in enums:
				enumData = sTrac['trac'].getEnum(enum)
				self.dests[dest]['trac'].addEnum(enumData)
		
	def mergeVersion(self):
		'''Merge the version values.'''
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			versions = sTrac['trac'].listVersions()
			for version in versions:
				versionData = sTrac['trac'].getVersion(version)
				self.dests[dest]['trac'].addVersion(versionData)
		
	def mergeComponent(self):
		'''Merge the components.'''
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			comps = sTrac['trac'].listComponents()
			for comp in comps:
				compData = sTrac['trac'].getComponent(comp)
				compData['owner'] = self._updateAuthor(compData['owner'])
				if compData['description']:
					compData['description'] = self._updateText(sTrac['name'], compData['description'])
				self.dests[dest]['trac'].addComponent(compData)
		
	def mergeTicket(self):
		'''Merge the tickets.'''
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			tickets = sTrac['trac'].listTickets()
			for ticket in tickets:
				ticketData = sTrac['trac'].getTicket(ticket)
				#Update the ticket details so it's consistent
				ticketData['id'] = str(int(ticketData['id']) + int(sTrac['ticket_pad']))
				ticketData['reporter'] = self._updateAuthor(ticketData['reporter'])
				ticketData['owner'] = self._updateAuthor(ticketData['owner'])
				for chg in ticketData['ticket_change']:
					if chg['field'] == 'comment':
						chg['newvalue'] = self._updateText(sTrac['name'], chg['newvalue'])
					chg['author'] = self._updateAuthor(chg['author'])
				for attachment in ticketData['attachment']:
					attachment['author'] = self._updateAuthor(attachment['author'])

				#Update the description if its out of date
				newText = self._updateText(sTrac['name'], ticketData['description'])
				if newText != ticketData['description']:
					newChg = {'ticket' : ticketData['id'], 'time' : time.time(), 'author' : 'tracmerge', 'field' : 'description'}
					newChg['oldvalue'] = ticketData['description']
					newChg['newvalue'] = newText
					ticketData['ticket_change'].append(newChg)
					ticketData['description'] = newText 
					ticketData['changetime'] = time.time()
				self.dests[dest]['trac'].addTicket(ticketData, sTrac['name'])
			print "%s's tickets padded by %s and added to %s" % (sTrac['name'], sTrac['ticket_pad'], dest)

	def mergeRepository(self):
		'''Add each source repository to the destination trac.'''
		for sTrac in self.sources.values():
			dest = sTrac['default_dest']
			repo = sTrac['trac'].getRepository()
			repo['name'] = sTrac['name']
			self.dests[dest]['trac'].addRepository(repo)
			print "%s's %s repository added to %s" % (sTrac['name'], repo['type'], dest)


def checkCollisions(*tracs):
	"""Returns a dictionary of collisions in all the elements of set of tracs."""
	debug = False
	allWikis = {}
	allComponents = {}
	allVersions = {}
	allMilestones = {}
	allVersions = {}
	allEnums = {}
	
	for trac in tracs:
		info = trac.getAllInfo()
		for page in info['wikiNames']:
			try:
				allWikis[page][0] += 1
				allWikis[page][1].append(trac.name)
			except KeyError:
				allWikis[page] = [1, [trac.name]]
		for comp in info['components']:
			try:
				allComponents[comp][0] += 1
				allComponents[comp][1].append(trac.name)
			except KeyError:
				allComponents[comp] = [1, [trac.name]]
		for mile in info['milestones']:
			try:
				allMilestones[mile][0] += 1
				allMilestones[mile][1].append(trac.name)
			except KeyError:
				allMilestones[mile] = [1, [trac.name]]
		for version in info['versions']:
			try:
				allVersions[version][0] += 1
				allVersions[version][1].append(trac.name)
			except KeyError:
				allVersions[version] = [1, [trac.name]]
		for enum in info['enums']:
			try:
				allEnums[enum][0] += 1
				allEnums[enum][1].append(trac.name)
			except KeyError:
				allEnums[enum] = [1, [trac.name]]
	collisions = {'wiki' : [], 'component' : [], 'milestone' : [], 'version' : []}
	for page, (cnt, where) in [x for x in sorted(allWikis.items(), 
	key=lambda x: x[1][0], reverse=True) if x[1][0] > 1]:
		collisions['wiki'].append((page, cnt, where)) 
		if debug:
			print "WIKI COLLISION: %sx '%s' in: %s" % (cnt, page, ', '.join(where))
	for comp, (cnt, where) in [x for x in sorted(allComponents.items(),
	key=lambda x: x[1][0], reverse=True) if x[1][0] > 1]: 
		collisions['component'].append((comp, cnt, where)) 
		if debug:
			print "COMPONENT COLLISION: %sx '%s' in: %s" % (cnt, comp, ', '.join(where))
	for mile, (cnt, where) in [x for x in sorted(allMilestones.items(),
	key=lambda x: x[1][0], reverse=True) if x[1][0] > 1]: 
		collisions['milestone'].append((mile, cnt, where)) 
		if debug:
			print "MILESTONE COLLISION: %sx '%s' in: %s" % (cnt, mile, ', '.join(where))
	for version, (cnt, where) in [x for x in sorted(allVersions.items(),
	key=lambda x: x[1][0], reverse=True) if x[1][0] > 1]: 
		collisions['version'].append((version, cnt, where)) 
		if debug:
			print "VERSION COLLISION: %sx '%s' in: %s" % (cnt, version, ', '.join(where))
	return collisions

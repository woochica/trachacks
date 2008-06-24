import tracmerge
import unittest

env2correct = {
	'components': [u'Thingie the first', u'Meh', u'Im bored', u'sleep'],
	 'enums': [(u'resolution', u'fixed'),
		   (u'resolution', u'invalid'),
		   (u'resolution', u'wontfix'),
		   (u'resolution', u'duplicate'),
		   (u'resolution', u'worksforme'),
		   (u'priority', u'blocker'),
		   (u'priority', u'critical'),
		   (u'priority', u'major'),
		   (u'priority', u'minor'),
		   (u'priority', u'trivial'),
		   (u'ticket_type', u'defect'),
		   (u'ticket_type', u'enhancement'),
		   (u'ticket_type', u'task'),
		   (u'priority', u'Meh'),
		   (u'resolution', u'complete'),
		   (u'severity', u'High'),
		   (u'severity', u'Low')],
	 'maxTicket': 2,
	 'milestones': [u'milestone4', u'Procrastination', u'Never'],
	 'versions': [u'1.0', u'2.0'],
	 'wikiNames': [u'WikiStart', u'Baz', u'BluRay', u'HDDVD']}
env1correct = {
	'components': [u'Thingie the first',
			u'Thingie the second',
			u'Thingie the third'],
	 'enums': [(u'resolution', u'fixed'),
		   (u'resolution', u'invalid'),
		   (u'resolution', u'wontfix'),
		   (u'resolution', u'duplicate'),
		   (u'resolution', u'worksforme'),
		   (u'priority', u'blocker'),
		   (u'priority', u'critical'),
		   (u'priority', u'major'),
		   (u'priority', u'minor'),
		   (u'priority', u'trivial'),
		   (u'ticket_type', u'defect'),
		   (u'ticket_type', u'enhancement'),
		   (u'ticket_type', u'task'),
		   (u'priority', u'Meh'),
		   (u'resolution', u'complete'),
		   (u'severity', u'High'),
		   (u'severity', u'Low')],
	 'maxTicket': 2,
	 'milestones': [u'Release 2.1',
			u"Here's a milestone for ya",
			u'Release 2.2',
			u'milestone4'],
	 'versions': [u'1.0', u'2.0'],
	 'wikiNames': [u'Foo', u'WikiStart', u'Bar', u'Baz']}
colcorrect = {
	'wiki': [(u'WikiStart', 2, [u'Test Project 1', u'Test Project 2']),
		(u'Baz', 2, [u'Test Project 1', u'Test Project 2'])],
	'version': [(u'2.0', 2, [u'Test Project 1', u'Test Project 2']),
		(u'1.0', 2, [u'Test Project 1', u'Test Project 2'])],
	'component': [(u'Thingie the first', 2, [u'Test Project 1', u'Test Project 2'])],
	'milestone': [(u'milestone4', 2, [u'Test Project 1', u'Test Project 2'])]}

class TracMergeUnitTest(unittest.TestCase):
	'''Verifies that TracMerge works appropriately'''
	def testInfo(self):
		'''Verify that we get the full and correct into from getAllInfo()'''
		env2 = tracmerge.Trac('testenv2')
		env2AllInfo = env2.getAllInfo()
		self.assertEqual(env2correct, env2AllInfo)

		env1 = tracmerge.Trac('testenv1')
		env1AllInfo = env1.getAllInfo()
		self.assertEqual(env1correct, env1AllInfo)

	def testCollision(self):
		env1 = tracmerge.Trac('testenv1')
		env2 = tracmerge.Trac('testenv2')
		self.assertEqual(colcorrect, tracmerge.checkCollisions(env1, env2))

if __name__ == '__main__':
	unittest.main()

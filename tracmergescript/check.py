import tracmerge


tracList = ('admin',
	'analytics',
	'bix',
	'ops',
	'panel',
	'pdl',
	'pollster',
	'projects',
	'special',
	'surveysys',
	'sysadmin',
	'voxpop',
	'rfk',)

tracs = []

for t in tracList:
	tracs.append(tracmerge.Trac('../oldtrac/%s' % t))


tracmerge.checkCollisions(*tracs)

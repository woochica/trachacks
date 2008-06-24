import tracmerge
import csv

#wiki rename map filename
wikiMapFilename = 'WikiRenames.csv'
#changesetMapFilename = 'RevRenames.csv'

#Destinations
DEST1 = 'Dest1'
DEST2 = 'Dest2'

#sources
TEST1 = 'Test1'
TEST2 = 'Test2'
TEST3 = 'Test3'

mergeConf = {
	'user_map' : {
		'chris@DOMAIN.COM' : 'chris',
	}
}
dests = {
    	DEST1 : {'path' : 'dest1',
		'db' : 'sqlite:db/trac.db',
		'repo_type' : 'hg',
		'repo_dir' : 'empty',
		'configs' : [
			('inherit', 'file', '/var/trac/common/conf/trac.ini'),
			('inherit', 'templates_dir', '/var/trac/common/templates/'),
			('ticket-custom', 'source', 'select'),
    			('ticket-custom', 'source.label', 'Source'),
    			('ticket-custom', 'source.options', '|Test1|Test2|Test3'), 
			('repositories', 'support/under_construction.type', 'hg'),
			('repositories', 'support/under_construction.dir', '/tmp/support/under_construction'),
    			],
    	},
    	DEST2 : {'path' : 'dest2',
		'db' : 'sqlite:db/trac.db',
		'repo_type' : 'hg',
		'repo_dir' : 'empty',
		'configs' : [
			('inherit', 'file', '/var/trac/common/conf/trac.ini'),
			('inherit', 'templates_dir', '/var/trac/common/templates/'),
    			],
    	},
}
sources = {
	TEST1 : {
		'path' : 'test/testenv1',
		'default_dest' : DEST1,
		'ticket_pad' : 1000,
        },

	TEST2 : {
		'path' : 'test/testenv2',
		'default_dest' : DEST2,
		'ticket_pad' : 1000,
        },
	TEST3 : {
		'path' : 'test/testenv3',
		'default_dest' : DEST2,
		'ticket_pad' : 2000,
	}, #close source
}

def main():
	
	wikiMap = csv.reader(open(wikiMapFilename))
	#skip the header
	wikiMap.next() 
	for rename in wikiMap:
		try:
			r_strac = rename[0].strip()
			r_spage = rename[1].strip()
			r_dtrac = rename[2].strip()
			r_dpage = rename[3].strip()
		except IndexError:
			continue
		if r_dtrac.endswith('?'):
			r_dtrac = r_dtrac[:-1]
		try:
			sources[r_strac]['wikimap'][r_spage] = (r_dtrac, r_dpage)
		except KeyError:
			sources[r_strac]['wikimap'] = {r_spage : (r_dtrac, r_dpage)}

	#changesetMap = csv.reader(open(changesetMapFilename))
	#skip the header
	#changesetMap.next() 
	#for rev in changesetMap:
	#	revTrac = rev[0].strip()
	#	oldRev = rev[1].strip()
	#	newRev = rev[2].strip()
	#	try:
	#		sources[revTrac]['revmap'].append((oldRev, newRev))
	#	except KeyError:
	#		sources[revTrac]['revmap'] = [(oldRev, newRev)]
	merge = tracmerge.MergeTracs(mergeConf, sources, dests)
	merge.initDestinations()
	merge.merge()

if __name__ == '__main__':
	main()

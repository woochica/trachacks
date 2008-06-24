import tracmerge
import csv
import example

sources = example.sources

output = csv.writer(open('wikiPageList.csv', 'w'))

for name, sTrac in sources.items():
	trac = tracmerge.Trac(sTrac['path'])
	pages = trac.listWikiPages()
	pages2 = [(name, x) for x in sorted(pages)]
	output.writerows(pages2)

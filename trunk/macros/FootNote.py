from StringIO import StringIO
from trac.util import escape
from trac.WikiFormatter import wiki_to_oneliner

footnote_set = 1
footnotes = []

def execute(hdf, args, env):
	global footnotes, footnote_set
	# Display and clear footnotes...
	if not args:
		out = StringIO()
		out.write('<div class="footnotes">\n');
		out.write('<hr style="width: 10%; padding: 0; margin: 1em 0 1em 0;"/>\n');
		out.write('<ol style="padding: 0 0 0 1em; margin: 0;">\n')
		for i, v in enumerate(footnotes):
			id = "%i.%i" % (footnote_set, i + 1)
			out.write('<li style="list-style: none;" id="FootNote%s"><a href="#FootNoteRef%s">%i.</a> %s</li>\n' % (id, id, i + 1, v))
		out.write('</ol>\n')
		out.write('</div>\n');
		footnotes = []
		footnote_set += 1
		return out.getvalue()
	else:
		id = len(footnotes) + 1
		try:
			id = int(args)
		except ValueError:
			footnotes.append(args)
		full_id = "%i.%i" % (footnote_set, id)
		return '<sup><a id="FootNoteRef%s" href="#FootNote%s">%i</a></sup>' % (full_id, full_id, id)

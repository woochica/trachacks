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
		out.write('<h4>Foot-notes:</h4>\n')
		out.write('<ol>\n')
		for i, v in enumerate(footnotes):
			out.write('<li id="FootNote%i.%i"><span class="footnotebody">%s</span></li>\n' % (footnote_set, i + 1, wiki_to_oneliner(v, hdf, env, env.get_db_cnx())))
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
		return '<sup><a href="#FootNote%i.%i">%i</a></sup>' % (footnote_set, id, id)

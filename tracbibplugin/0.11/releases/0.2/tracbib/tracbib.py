from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.attachment import Attachment
from trac.env import Environment
from genshi.builder import tag
from trac.wiki.model import WikiPage
from trac.wiki.formatter import WikiProcessor
from trac.util.text import to_unicode

import re
import _bibtex

BIBDB = 'bibtex - database'
CITELIST = 'referenced elements'

BIBTEX_KEYS = [
    'author',
    'editor',
    'title',
    'intype',
    'booktitle',
    'edition',
    'series',
    'journal',
    'volume',
    'number',
    'organization',
    'institution',
    'publisher',
    'school',
    'howpublished',
    'day',
    'month',
    'year',
    'chapter',
    'volume',
    'paper',
    'type',
    'revision',
    'isbn',
    'pages',
]
def extract_entries(text):
	bibdb = {}
	bibfile = _bibtex.open_string('temporary archive',text,True)
	entry = _bibtex.next(bibfile)
	if entry == None :
		return None
	
	while entry != None:
		contentdb = {}
		items = entry[4]
		key = entry[0]
		for k in items.keys():
			contentdb[k] = _bibtex.expand(bibfile, items[k],-1)[2]
		
		bibdb[key] = contentdb
		entry = _bibtex.next(bibfile)
	
	return bibdb

class BibAddMacro(WikiMacroBase):
	implements(IWikiMacroProvider)

	def expand_macro(self,formatter,name,content):
		args, kwargs = parse_args(content, strict=False)
		if len(args) != 1:
			raise TracError('[[Usage: BibAdd(source:file@rev) or BibAdd(attachment:wikipage/file) or BibAdd(attachment:file)]] ')
		
		whom = re.compile(":|@").split(args[0])
		file = None
		rev = None
		pos = None
		path = None
		entry = None
		entries = None

		# load the file from the repository
		if whom[0] == 'source':
			if len(whom) < 2:
				raise TracError('[[Missing argument(s) for citing from source; Usage: BibAdd(source:file@rev)]]')
			elif len(whom) == 2:
				rev = 'latest'
			else:
				rev = whom[2]

			file = whom[1]

			repos = self.env.get_repository()
			try:
				bib = repos.get_node(file, rev)
				file = bib.get_content()
				string = file.read()
			finally:
				repos.close()
	
		# load the file from the wiki attachments
		elif whom[0] == 'attachment':
			if (len(whom) != 2):
				raise TracError('Wrong syntax for environment \'attachment\'; Usage: BibAdd(attachment:file)')

			pos = 'wiki'
			page = None
			file = whom[1]
			path_info = whom[1].split('/',1)
			if len(path_info) == 2:
				page = path_info[0]
				file = path_info[1]
			else:
				page = formatter.req.args.get('page')
				if (page == None):
					page = 'WikiStart'

			bib = Attachment(self.env,pos,page,file)
			file = bib.open()
			string = file.read()

		# use wiki page itself
		elif whom[0] == 'wiki':
			if (len(whom) != 2):
				raise TracError('Wrong syntax for environment \'wiki\'; Usage BibAdd(wiki:page)')
			
			page = WikiPage(self.env,whom[1])
			if page.exists:
				if '{{{' in page.text and '}}}' in page.text:
					tmp = re.compile('{{{|}}}',2).split(page.text)
					string = tmp[1]
				else:
					raise TracError('No code block on page \'' + whom[1] + '\' found.')
			else:
				raise TracError('No wiki page named \'' + whom[1] + '\' found.')
		else:
			raise TracError('Unknown location \''+ whom[0] +'\'')

		entries = extract_entries(string)
		if entries == None:
			raise TracError('No entries from file \''+ args[0] +'\' loaded.')
		
		bibdb = getattr(formatter, BIBDB,{})
		bibdb.update(entries)
		setattr(formatter,BIBDB,bibdb)

class BibCiteMacro(WikiMacroBase):
	implements(IWikiMacroProvider)
	
	def expand_macro(self,formatter,name,content):

		args, kwargs = parse_args(content, strict=False)

		if len(args) > 1:
			raise TracError('Usage: [[BibCite(BibTexKey)]]')
		elif len(args) < 1:
			raise TracError('Usage: [[BibCite(BibTexKey)]]')
		
		key = args[0];

		bibdb = getattr(formatter, BIBDB,{})
		citelist = getattr(formatter, CITELIST,[])
		
		if key not in citelist:
			citelist.append(key)
			setattr(formatter,CITELIST,citelist)
		
		index = citelist.index(key) + 1
	
		return ''.join(['[', str(tag.a(name='cite_%s' % key)), str(tag.a(href='#%s' % key)('%d' % index)), ']'])

class BibNoCiteMacro(WikiMacroBase):
	implements(IWikiMacroProvider)
	
	def expand_macro(self,formatter,name,content):

		args, kwargs = parse_args(content, strict=False)

		if len(args) > 1:
			raise TracError('Usage: [[BibNoCite(BibTexKey)]]')
		elif len(args) < 1:
			raise TracError('Usage: [[BibNoCite(BibTexKey)]]')
		
		key = args[0];

		bibdb = getattr(formatter, BIBDB,{})
		citelist = getattr(formatter, CITELIST,[])
		
		if key not in citelist:
			citelist.append(key)
			setattr(formatter,CITELIST,citelist)
	
		return


class BibRefMacro(WikiMacroBase):
	implements(IWikiMacroProvider)

	def expand_macro(self,formatter,name,content):
		citelist = getattr(formatter, CITELIST,[])
		bibdb = getattr(formatter, BIBDB,{})

		page = WikiPage(self.env,'BibTex')
		if page.exists:
			if '{{{' in page.text and '}}}' in page.text:
				tmp = re.compile('{{{|}}}',2).split(page.text)
				bibdb.update(extract_entries(tmp[1]))
				setattr(formatter,BIBDB,bibdb)

		str = ''
		for k in citelist:
			if bibdb.has_key(k) == False:
				str +='No entry ' + k + ' found.\n'
		if str != '':
			raise TracError('[[' + str + ']]')

		l = []
		for k in citelist:
			content = ''
			for bibkey in BIBTEX_KEYS:
				if bibdb[k].has_key(bibkey):
					content +=bibdb[k][bibkey] + ', '
			if bibdb[k].has_key('url') == False:
				l.append(tag.li(tag.a(name=k), tag.a(href='#cite_%s' % k)('^') ,content))
			else:
				url = bibdb[k]['url']
				l.append(tag.li(tag.a(name=k), tag.a(href='#cite_%s' % k)('^') ,content, tag.br(),tag.a(href=url)(url)))

		ol = tag.ol(*l)
		tags = []
		tags.append(tag.h1(id='References')('References'))
		tags.append(ol)

		return tag.div(id='References')(*tags)

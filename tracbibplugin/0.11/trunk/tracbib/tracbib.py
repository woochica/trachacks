from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.attachment import Attachment
from trac.env import Environment
from genshi.builder import tag

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


class BibAddMacro(WikiMacroBase):
	implements(IWikiMacroProvider)

	def expand_macro(self,formatter,name,content):

		args, kwargs = parse_args(content, strict=False)

		if len(args) != 1:
			raise TracError('[[Usage: TracBib(source:file@rev) or TracBib(attachment:wikipage/file) or TracBib(attachment:file)]] ')
			
		
		whom = re.compile(":|@").split(args[0])
		file = None
		rev = None
		pos = None
		path = None
		entry = None
		
		bibdb = getattr(formatter, BIBDB,{})

		# load the file from the repository
		if whom[0] == 'source':
			if len(whom) < 2:
				raise TracError('[[Missing argument(s) for citing from source: TracBib(source:file@rev)]]')
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
				bibfile = _bibtex.open_string('temporary archive',string,True)
				entry = _bibtex.next(bibfile)
				if entry == None :
					raise TracError('No entries from bibfile loaded.')
			finally:
				repos.close()
	
		# load the file from the wiki attachments
		elif whom[0] == 'attachment':
			if (len(whom) != 2):
				raise TracError('[[Unknown Format.]]')

			pos = 'wiki'
			page = None
			file = whom[1]
			path_info = whom[1].split('/',1)
			if len(path_info) == 2:
				page = path_info[0]
				file = path_info[1]
			else:
				path_info = formatter.req.path_info.split('/',2)
				page = path_info[2]

			bib = Attachment(self.env,pos,page,file)
			file = bib.open()
			string = file.read()
			bibfile = _bibtex.open_string('temporary archive',string,True)
			entry = _bibtex.next(bibfile)
			if entry == None :
				raise TracError('No entries from bibfile loaded.')

		elif whom[0] == 'wiki':
			raise TracError('[[This release does not support loading bibtex entries directly from a wiki page.]]')

		else:
			raise TracError('[[Unknown location.]]')

		while entry != None:
			contentdb = {}
			items = entry[4]
			key = entry[0]
			for k in items.keys():
				contentdb[k] = _bibtex.expand(bibfile, items[k],-1)[2]
			
			bibdb[key] = contentdb
			entry = _bibtex.next(bibfile)
	
		setattr(formatter,BIBDB,bibdb)

class BibCiteMacro(WikiMacroBase):
	implements(IWikiMacroProvider)
	
	def expand_macro(self,formatter,name,content):

		args, kwargs = parse_args(content, strict=False)

		if len(args) > 1:
			raise TracError('Usage: [[BibCite(BibTex-key)]]')
		elif len(args) < 1:
			raise TracError('Usage: [[BibCite(BibTex-key)]]')
		
		key = args[0];

		bibdb = getattr(formatter, BIBDB,{})
		citelist = getattr(formatter, CITELIST,[])
		myentry = ''
		
		if key not in citelist:
			if bibdb.has_key(key) == False:
				raise TracError('No entry ' + key + ' found.')
			citelist.append(key)
			setattr(formatter,CITELIST,citelist)
		
		index = citelist.index(key) + 1
		db = bibdb[key]
	
		return ''.join(['[', str(tag.a(name='cite_%s' % key)), str(tag.a(href='#%s' % key)('%d' % index)), ']'])

class BibNoCiteMacro(WikiMacroBase):
	implements(IWikiMacroProvider)
	
	def expand_macro(self,formatter,name,content):

		args, kwargs = parse_args(content, strict=False)

		if len(args) > 1:
			raise TracError('Usage: [[BibNoCite(BibTex-key)]]')
		elif len(args) < 1:
			raise TracError('Usage: [[BibNoCite(BibTex-key)]]')
		
		key = args[0];

		bibdb = getattr(formatter, BIBDB,{})
		citelist = getattr(formatter, CITELIST,[])
		myentry = ''
		
		if key not in citelist:
			if bibdb.has_key(key) == False:
				raise TracError('No entry ' + key + ' found.')
			citelist.append(key)
			setattr(formatter,CITELIST,citelist)
		
		db = bibdb[key]
	
		return


class BibRefMacro(WikiMacroBase):
	implements(IWikiMacroProvider)

	def expand_macro(self,formatter,name,content):
		citelist = getattr(formatter, CITELIST,[])
		bibdb = getattr(formatter, BIBDB,{})

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

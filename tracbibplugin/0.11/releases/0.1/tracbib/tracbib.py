from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase
from trac.attachment import Attachment
from trac.env import Environment
from genshi.builder import tag
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

		if len(args) > 2 or len(args) <1:
			raise TracError('[[Usage: TracBib(file,revision) or TracBib(file)]] ')
		
		file = args[0]
		rev = None
		entry = None
		
		bibdb = getattr(formatter, BIBDB,{})

		# load the file from the repository
		if len(args) == 2:
			rev = args[1]

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
		elif len(args) == 1:
			path_info = formatter.req.path_info.split('/',2)
			bib = Attachment(self.env,'wiki',path_info[2],file)
			file = bib.open()
			string = file.read()
			bibfile = _bibtex.open_string('temporary archive',string,True)
			entry = _bibtex.next(bibfile)
			if entry == None :
				raise TracError('No entries from bibfile loaded.')

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

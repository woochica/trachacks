""" Citation plugin for Trac.
    
    Gives wikipages the equivalent to LaTeX's \cite{} and \makeindex commands.
    
    Used http://www.ctan.org/get/macros/latex/contrib/IEEEtran/bibtex/IEEEexample.bib
    as a starting point for the keywords.
    
    For possible improvement ideas see:
    http://www.trac-hacks.org/ticket/453
"""
from genshi.builder import tag
from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase


# url is special.
SEQUENCE = [
    'author',
    'assignee',
    'nationality',
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
    'language',
    'address',
    # 'url',
    'howpublished',
    'dayfiled',
    'monthfiled',
    'yearfiled',
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
    'note',
    'key'
]

FORMAT = {
    'author': '%s',
    'assignee': '%s',
    'nationality': '%s',
    'editor': '%s',
    'title': '%s',
    'intype': '%s',
    'booktitle': '%s',
    'edition': '%s',
    'series': '%s',
    'journal': '%s',
    'volume': '%s',
    'number': '%s',
    'organization': '%s',
    'institution': '%s',
    'publisher': '%s',
    'school': '%s',
    'language': '%s',
    'address': '%s',
    'howpublished': '%s',
    'dayfiled': '%s',
    'monthfiled': '%s',
    'yearfiled': '%s',
    'day': '%s',
    'month': '%s',
    'year': '%s',
    'chapter': '%s',
    'volume': '%s',
    'paper': '%s',
    'type': '%s',
    'revision': '%s',
    'isbn': '%s',
    'pages': 'pages %s',
    'note': '%s',
    'key': '%s'
}

BIBTEX_SEQUENCE = [
    'author',
    'assignee',
    'nationality',
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
    'language',
    'address',
    'url',
    'howpublished',
    'dayfiled',
    'monthfiled',
    'yearfiled',
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
    'note',
    'key'
]

# We can be more creative with the output, abbreviation, capitalization, etc.
def format_author(author):
    return '{%s}' % author

BIBTEX_FORMAT = {
    'author': format_author,
    'assignee': '%s',
    'nationality': '%s',
    'editor': '%s',
    'title': '%s',
    'intype': '%s',
    'booktitle': '%s',
    'edition': '%s',
    'series': '%s',
    'journal': '%s',
    'volume': '%s',
    'number': '%s',
    'organization': '%s',
    'institution': '%s',
    'publisher': '%s',
    'school': '%s',
    'language': '%s',
    'address': '%s',
    'howpublished': '%s',
    'dayfiled': '%s',
    'monthfiled': '%s',
    'yearfiled': '%s',
    'day': '%s',
    'month': '%s',
    'year': '%s',
    'chapter': '%s',
    'volume': '%s',
    'paper': '%s',
    'type': '%s',
    'revision': '%s',
    'isbn': '%s',
    'pages': '%s',
    'note': '%s',
    'key': '%s',
    'url': '%s'
}

CITE_LIST = '_citemacro_cite_list'
CITE_DICT = '_citemacro_cite_dict'

def string_keys(d):
    """ Convert unicode keys into string keys, suiable for func(**d) use.
    """
    sdict = {}
    for key, value in d.items():
        sdict[str(key)] = value
    
    return sdict


class CiteMacro(WikiMacroBase):
    
    implements(IWikiMacroProvider)
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        """
        """
        args, kwargs = parse_args(content, strict=False)
        kwargs = string_keys(kwargs)
        
        cite_list = getattr(formatter, CITE_LIST, [])
        cite_dict = getattr(formatter, CITE_DICT, {})
        
        if len(args) == 1:
            label = args[0]
            description = ''
        
        if len(args) == 2:
            label = args[0]
            description = args[1]
        
        # Allow for extra parameters, people can use it to store BibTeX data.
        if len(args) == 0:
            raise TracError('At the very least a `label` is required.')
        
        # `makeindex` will not make sense to non-LaTeX users.
        if label == 'references':
            h = kwargs.get('h', '1')
            backref = kwargs.get('backref')
            
            tags = []
            if h == '1':
                root = tag.h1
            elif h == '2':
                root = tag.h2
            elif h == '3':
                root = tag.h3
            elif h == '4':
                root = tag.h4
            else:
                root = tag.h5
            
            tags.append(root(id='References')('References'))
            
            li = []
            for index, label in enumerate(cite_list):
                description, params = cite_dict[label]
                
                if description:
                    line = [description]
                else:
                    line = []
                
                for key in SEQUENCE:
                    value = params.get(key)
                    if value:
                        line.append(FORMAT[key] % value)
                
                entry = ', '.join(line)
                
                url = params.get('url')
                
                if entry and url:
                    entry += ','
                
                if entry:
                    if url:
                        if backref:
                            li.append(tag.li(tag.a(name=label), tag.a(href='#cite_%s' % label)('^'), ' ', entry, tag.br(), tag.a(href=url)(url)))
                        else:
                            li.append(tag.li(tag.a(name=label), entry, tag.br(), tag.a(href=url)(url)))
                    else:
                        if backref:
                            li.append(tag.li(tag.a(name=label), tag.a(href='#cite_%s' % label)('^'), ' ', entry))
                        else:
                            li.append(tag.li(tag.a(name=label), entry))
                else:
                    if url:
                        if backref:
                            li.append(tag.li(tag.a(name=label), tag.a(href='#cite_%s' % label)('^'), ' ', tag.a(href=url)(url)))
                        else:
                            li.append(tag.li(tag.a(name=label), tag.a(href=url)(url)))
            
            ol = tag.ol(*li)
            tags.append(ol)
            
            # This is ugly but it is easy.
            return tag.div(id='References')(*tags)
        
        elif label == 'bibtex':
            indent = kwargs.get('indent', 2)
            try:
                indent = int(indent)
                indent = (indent, 0)[indent < 0]
                indent = (indent, 8)[indent > 8]
            except ValueError:
                intent = 2
            
            references = []
            for index, label in enumerate(cite_list):
                description, params = cite_dict[label]
                reftype = params.get('reftype', 'Book')
                
                reference = []
                reference.append('@%s{%s' % (reftype, label))
                for key in BIBTEX_SEQUENCE:
                    value = params.get(key)
                    if value:
                        bibtex_formatter = BIBTEX_FORMAT[key]
                        if callable(bibtex_formatter):
                            value = bibtex_formatter(value)
                        else:
                            value = bibtex_formatter % value
                        
                        reference.append(',\n%s%s = "%s"' % (' ' * indent, key, value))
                
                if len(reference) == 1:
                    reference.append(',')
                
                reference.append('\n};')
                references.append(''.join(reference))
            
            if 'class' in kwargs:
                kwargs['class_'] = kwargs.pop('class')
            
            return tag.pre('\n\n'.join(references), **kwargs)
        
        else:
            if label not in cite_list:
                cite_list.append(label)
                cite_dict[label] = (description, kwargs)
                
                setattr(formatter, CITE_LIST, cite_list)
                setattr(formatter, CITE_DICT, cite_dict)
                backref = True
            else:
                backref = False
            
            index = cite_list.index(label) + 1
            
            if backref:
                return ''.join(['[', str(tag.a(name='cite_%s' % label)), str(tag.a(href='#%s' % label)('%d' % index)), ']'])
            else:
                return ''.join(['[', str(tag.a(href='#%s' % label)('%d' % index)), ']'])

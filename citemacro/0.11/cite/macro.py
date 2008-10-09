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
    'pages': 'pages %s',
    'note': '%s',
    'key': '%s'
}

CITE_LIST = '_citemacro_cite_list'
CITE_DICT = '_citemacro_cite_dict'

class CiteMacro(WikiMacroBase):
    
    implements(IWikiMacroProvider)
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        """
        """
        args, kwargs = parse_args(content, strict=False)
        
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
        if label != 'references':
            if label not in cite_list:
                cite_list.append(label)
                cite_dict[label] = (description, kwargs)
                
                setattr(formatter, CITE_LIST, cite_list)
                setattr(formatter, CITE_DICT, cite_dict)
            
            index = cite_list.index(label) + 1
            return ''.join(['[', str(tag.a(href='#%s' % label)('%d' % index)), ']'])
        
        else:
            h = kwargs.get('h', '1')
            
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
                
                if entry:
                    entry = entry + ','
                
                url = params.get('url')
                
                if entry:
                    if url:
                        li.append(tag.li()(tag.a(name=label), entry, tag.br(), tag.a(href=url)(url)))
                    else:
                        li.append(tag.li()(tag.a(name=label), entry))
                else:
                    if url:
                        li.append(tag.li()(tag.a(name=label), tag.a(href=url)(url)))
            
            ol = tag.ol()(*li)
            tags.append(ol)
            
            # This is ugly but it is easy.
            return tag.div(id='References')(*tags)

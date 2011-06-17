from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args
from genshi.builder import tag
from genshi import Markup
from model import *
from web_ui import *

CITELIST = 'referenced elements'

class ZotCiteMacro(WikiMacroBase):
    implements(IWikiMacroProvider)
    
    def render_macro(self, request,name,content):
        return self.expand_macro(request,name,content)
    
    def expand_macro(self,formatter,name,content):
    
        args, kwargs = parse_args(content)
        known_command = ['ait','authorintext']
        args = [a.strip() for a in args]
        key_args = [a for a in args if a not in known_command]
        command_args = [a for a in args if a in known_command]
        if len(key_args) < 1:
            raise TracError('Usage: [[ZotCite(key)]]')
        
        citelist = getattr(formatter, CITELIST,[])
        
        keys = []
        for key in key_args: 
            k = []
            if key[0:2] == '0_':
                k = key[2:10]
            else:
                k = key[0:8]
            keys.append(k)
            if k not in citelist:
                citelist.append(k)
        setattr(formatter,CITELIST,citelist)     
        
        model = ZoteroModelProvider(self.env)
        item_id = model.get_items_id( keys )
        if not item_id:
            raise TracError( 'Some key(s) in ' + ', '.join(keys) + ' can not be found')
        item_cites = model.get_item_cites(item_id)
        req = formatter.req
        if 'ait' in args or 'authorintext' in command_args:
            
            return '; '.join([str(tag.span( tag.span(c + ' (' ), tag.a(y, 
                        href = req.href.zotero('item/' + str(id)) ), tag.span(')' ) ) ) for id, c, y in item_cites])
        return ''.join( ['(', 
                   '; '.join([str(tag.a(c + ', ' + y, 
                        href = req.href.zotero('item/' + str(id)) ) ) for id, c, y in item_cites]),')'])

class ZotRefMacro(WikiMacroBase):
  implements(IWikiMacroProvider)

  def render_macro(self, request,name,content):
    return self.expand_macro(request,name,content)

  def expand_macro(self,formatter,name,content):
    citelist = getattr(formatter, CITELIST,[])
    fields = ['itemTypeID','firstCreator','year', 'publicationTitle','volume','issue','pages','title','url']
    model = ZoteroModelProvider(self.env)
    item_ids = model.get_items_id( citelist )
    item_data = model.get_item_fields(item_ids,fields)
    refs = []

    for itemID, itemTypeID, firstCreator, year, publicationTitle, volume, issue, pages, title, url in item_data:
        prefix = ''
        if firstCreator and firstCreator != 'None':
            prefix += firstCreator
        if year and year != 'None':
            prefix += ' ' + year + '. '
        titlehref = ''
        if title and title != 'None':
            titlehref = tag.a(title, href = formatter.req.href.zotero('item/' + str(itemID)))
        suffix = ''
        if publicationTitle and publicationTitle != 'None':
            suffix += '. ' + publicationTitle
        if volume and volume != 'None':
            suffix += ', ' + str(volume)
        if pages and pages != 'None':
            suffix += ': ' + pages + '.'
        ref = []
        if url and url != 'None':
            ref = tag.li( tag.span( prefix ), tag.span(titlehref), tag.span(suffix),
                    tag.br(),tag.span(tag.a(url, href=url ),style = 'font-size:x-small;') )
        else: 
            ref = tag.li( tag.span( prefix ), tag.span(titlehref), tag.span(suffix) )
    
        refs.append(ref)

    return tag.div(tag.ol(refs),id='References')
class ZotRelatedMacro(WikiMacroBase):
    implements(IWikiMacroProvider)
    
    def render_macro(self, request,name,content):
        return self.expand_macro(request,name,content)
    
    def expand_macro(self,formatter,name,content):
        args, kwargs = parse_args(content)
        
        if len(args) < 1:
            raise TracError('Usage: [[ZotRelated(key)]]')
        if len(args) > 1:
            raise TracError('Usage: [[ZotRelated(key)]]')
        citelist = getattr(formatter, CITELIST,[])
        
        key = args
        if key[0:2] == '0_':
            key = key[2:10]
        else:
            key = key[0:8]
        fields = self.env.config.get('zotero', 'fields','firstCreator, year, publicationTitle, title' )
        fields = fields.split(',')
        fields = [f.strip() for f in fields]
        labels = self.env.config.get('zotero', 'labels','Authors, Year, Publication, Title' )
        labels = labels.split(',')
        labels = [f.strip() for f in labels]
        
        model = ZoteroModelProvider(self.env)
        item_ids = model.get_items_id( key )
        rids = model.get_related(item_ids)
        rids_all = []

        for id, lid in rids:
            if str(id) == str(item_ids[0]):
                rids_all.append(lid)
            else:
                rids_all.append(id)

        if len(rids_all) > 0:
            item_mata = model.get_item_fields(rids_all,fields)
            return render_refs_box(self,formatter.req, rids_all)
    
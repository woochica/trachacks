from model import *
from trac.core import *
from trac.util.datefmt import format_datetime
from trac.web.api import IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            ITemplateStreamFilter, \
                            add_stylesheet, add_ctxtnav, add_link, add_script
from trac.search import ISearchSource, shorten_result
from trac.util.presentation import Paginator
from trac.versioncontrol.api import Node
from trac.perm import IPermissionRequestor
from trac.util import Markup, escape
from trac.versioncontrol.web_ui.util import *
from trac.mimeview.api import Mimeview
from genshi.filters.transform import Transformer, StreamBuffer
from genshi.builder import tag as builder
from trac.wiki.formatter import extract_link
from trac.mimeview import Context
from genshi.builder import tag
import re
import posixpath
import os
import string
from fnmatch import fnmatch
import sqlite3
from trac.cache import cached
from trac.wiki.formatter import format_to, format_to_oneliner
from trac.mimeview import Context

class TracZoteroRequestHandler(Component):
    implements( ITemplateStreamFilter, IPermissionRequestor, 
        IRequestHandler, ITemplateProvider, INavigationContributor)
    collectiontree = []
    field_mapping = {}
    field_mapping['journalAbbreviation'] = 'Journal Abbr'
    field_mapping['archiveLocation'] = 'Archive Loc.'
    field_mapping['callNumber'] = 'Call Number'
    field_mapping['libraryCatalog'] = 'Lib. Catalog'
    field_mapping['accessDate'] = 'Access'
    field_mapping['url'] = 'URL'
    def get_active_navigation_item(self, req):
        if 'ZOTERO' in req.perm:
            return 'zotero'

    def get_navigation_items(self, req):
        if 'ZOTERO' in req.perm:
            label = "Zotero"
            yield ('mainnav', 'zotero',
                   builder.a(label, href=req.href.zotero()) )
    def get_permission_actions(self):
        yield 'ZOTERO'
    def filter_stream(self, req, method, filename, stream, data):
        # Get path
        if filename == 'zotero.html':
            #raise Exception(item_exist(2))
            return stream
        return stream

    

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('zt', resource_filename(__name__, 'htdocs'))]
    def match_request(self, req):
        return req.path_info.startswith('/zotero')
    def process_request(self, req):
        add_script(req, 'zt/jquery.treeview/lib/jquery.js')
        add_script(req, 'zt/jquery.treeview/lib/jquery.cookie.js')
        add_script(req, 'zt/jquery.treeview/jquery.treeview.js')
        add_script(req, 'zt/jquery.treeview/jquery.browser.js')
        add_stylesheet(req, 'zt/jquery.treeview/jquery.treeview.css')
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'common/css/browser.css')
        
        add_ctxtnav(req, "Start", href = req.href.zotero())
        add_ctxtnav(req, "Search", href = req.href.zotero('search'))
        add_ctxtnav(req, "Restart", href = req.href.zotero('restart'))
        
        
        fields = self.env.config.get('zotero', 'fields','firstCreator, year, publicationTitle, title' )
        fields = fields.split(',')
        fields = [f.strip() for f in fields]
        labels = self.env.config.get('zotero', 'labels','Authors, Year, Publication, Title' )
        labels = labels.split(',')
        labels = [f.strip() for f in labels]
        
        data = {}

        # Add colection tree. this tree for all pages
        model = ZoteroModelProvider(self.env)
        col_root = model.get_root_collections()
        if not self.collectiontree:
            self.collectiontree = self.render_col_tree(req, col_root, model)
        data['collectiontree'] = self.collectiontree
        
        # parse command and page name
        command, pagename = self._parse_path(req)
        
        # for home page
        if not command:
            data['home'] = generate_home(self, req)
        # for collection
        elif command == 'collection':

            order = req.args.get('order', 'year')
            desc = req.args.get('desc', '')
            item_ids = []
            if pagename:
                item_ids = model.get_child_item(pagename)
            else:
                item_ids = model.get_all_item(True, [], False)
            items_data = render_refs_box(self, req, item_ids, order = order, desc = desc, 
                headhref=True,command=command,page=pagename )
            
            data['items'] = items_data
        
        # for item
        elif command == 'item' and pagename:
            add_stylesheet(req, 'common/css/diff.css')
            model = ZoteroModelProvider(self.env)
            creators = model.get_creators(pagename)
            field_value = model.get_item_field_value(pagename)
            
            known_fields = ['volume', 'issue', 'publicationTitle', 'pages','title','date','abstractNote']
            field_value_dic_known = {}
            field_value_dic_other = []
            for iid, fid, value, itid, order, fn in field_value:
                if fn in known_fields:
                    field_value_dic_known[fn] = [iid, fid, value, itid, order]
                else:
                    field_value_dic_other.append([iid, fid, value, itid, order, fn])
            
            item = []
            date_fields = ['dateAdded','dateModified','key','firstCreator','year']
            item_date = model.get_item_fields([pagename],date_fields)
            item_date = item_date[0]
            key = {}
            key['name'] = 'Cite Key:'
            cite_key = '[[ZotCite(' + item_date[3] + '(' +item_date[4]+item_date[5]+'))]]'
            key['value'] = cite_key.replace(' ', '')
            item.append(key)
            # for author
            author = {}
            author['name'] = 'Authors:'
            author['value'] = ''
            if creators:
                value = []
                for id, cid, f, l in creators:
                    v = tag.a( l + ' ' + f, href = req.href.zotero('search',author=str(cid) ) )
                    value.append(v)
                    value.append(tag.span('; '))
                value.pop()
                author['value'] = tag.span( value )
            item.append(author)
            # title 
            title = {}
            title['name'] = 'Title:'
            title['value'] = ''
            if field_value_dic_known.has_key('title'):
                title['value'] = field_value_dic_known['title'][2]
            item.append(title)
            
            # publisher
            publisher = {}
            publisher['name'] = 'Publication:'
            value = []
            if field_value_dic_known.has_key('publicationTitle'):
                publicationTitle = field_value_dic_known['publicationTitle'][2]
                value.append(tag.a(publicationTitle,
                    href=req.href.zotero('search',publisher=publicationTitle )))
            if field_value_dic_known.has_key('date'):  
                year = field_value_dic_known['date'][2]
                year = year[0:4]
                value.append(tag.span('. '))
                value.append(tag.a(year,
                    href=req.href.zotero('search',year=year )))
            if field_value_dic_known.has_key('volume'):
                value.append( tag.span(', '+field_value_dic_known['volume'][2]))
            if field_value_dic_known.has_key('issue'):
                value.append( tag.span(' ('+field_value_dic_known['issue'][2], ')'))
            if field_value_dic_known.has_key('pages'):
                value.append( tag.span(': '+field_value_dic_known['pages'][2]))
            publisher['value'] =  tag.span(value)
            item.append(publisher)
            # abstract
            if field_value_dic_known.has_key('abstractNote'):
                abstract = {}
                abstract['name'] = 'Abstract:'
                abstract['value'] = format_to(self.env, [],
                    Context.from_request(req, 'zotero'), 
                    field_value_dic_known['abstractNote'][2])
                
                item.append(abstract)
            # other fields
            for iid, fid, value, itid, order, fn in field_value_dic_other:
                field = {}
                if self.field_mapping.has_key(fn):
                    field['name'] = self.field_mapping[fn] + ':'
                else:
                    field['name'] = fn + ':'
                if fn == 'url':
                    field['value'] = tag.a(value, href=value)
                elif fn == 'DOI':
                    field['value'] = tag.a(value, href='http://dx.doi.org/'+value)
                else:
                    wiki_tag = format_to_oneliner(self.env,Context.from_request(req, 'zotero'), value)
                    field['value'] = wiki_tag
                    
                item.append(field)
            # for added and modifed time
            # for added time
            add_date = {}
            add_date['name'] = 'Date Added:'
            add_date['value'] = item_date[1]
            item.append(add_date)
            # for modified time
            modified_date = {}
            modified_date['name'] = 'Modified:'
            modified_date['value'] = item_date[2]
            item.append(modified_date)
            # For attachment
            altype = self.env.config.get('zotero', 'attachmentlink','web' )
        
            att = model.get_attachment([pagename])

            if att:
                attachment = {}
                attachment['name'] = 'Attachment:'
                a_value = []
                for a in att:
                    file_name = a[3]
                    file_name = file_name[8:]
                    href = 'zotero://attachment/'+ a[1]+'/'
                    if altype == 'web':
                        path = self.env.config.get('zotero', 'path' )
                        
                        href = req.href.chrome('site',path,'storage',a[4],file_name)
                    a_value.append(tag.a(file_name, href = href))
                    a_value.append(tag.br())
                a_value.pop()
                attachment['value'] = tag.span( a_value )
                item.append(attachment)
            
            data['item'] = item
            
            # Related items
            rids = model.get_related([pagename])
            rids_all = []
            for id, lid in rids:
                if str(id) == pagename:
                    rids_all.append(lid)
                else:
                    rids_all.append(id)
            
            if len(rids_all) > 0:
                data['related'] = render_refs_box(self,req, rids_all)
        # for item
        elif command == 'search':
            author = req.args.get('author', '')
            year = req.args.get('year', '')
            publisher = req.args.get('publisher','')
            order = req.args.get('order', 'year')
            desc = req.args.get('desc', '')
            model = ZoteroModelProvider(self.env)
            ids = []
            
            if author:
                ids = model.search_by_creator([author])
            elif year:
                ids = model.search_by_year([year])
            elif publisher:
                ids = model.search_by_publisher([publisher])
            items_data = render_refs_box(self, req, ids, order = order, desc = desc, 
                headhref=True,command=command,page=pagename )
            
            data['items'] = items_data
        elif command == 'cloud':
            type = req.args.get('t', '')
            data['cloud'] = render_cloud(self, req, type )
        elif command == 'restart':
            model = ZoteroModelProvider(self.env)
            model.restart()
            collectiontree=[]
            req.redirect(req.href.zotero())
        return 'zotero.html', data, None
    
    def render_col_tree(self, req, col_root, model):
        return tag.div( 
            tag.div( 
                tag.a( 'Collapse All', href = '?#' ), ' | ',
                tag.a( 'Expand All', href = '?#' ), 
                id = 'sidetreecontrol', style = 'font-size:xx-small;'),
            tag.div( tag.a( 'Library', href = req.href.zotero('collection') ) ),      
            self.render_child_col( req, col_root, model ),
            id="coltree", class_="treeview")
    def render_child_col(self, req, col_root, model ):
        node_ul = tag.ul()
        for id, name, pid, ischildcol, ischilditem in col_root:
            node_li = tag.li( tag.a( name, href = req.href.zotero('collection/'+str(id))) )
            if ischildcol:
                child_col = model.get_child_collections(id)
                node_li.append( self.render_child_col(req, child_col, model) )
            node_ul.append(node_li)
        return node_ul 
    def _parse_path(self, req):
        path = req.path_info
        path_items = path.split('/')
        path_items = [item for item in path_items if item] 
        command = pagename = ''
        if not path_items or len(path_items) == 1:
            pass # emtpy default for return is fine
        elif len(path_items) > 1 and path_items[1].lower() in ['collection', 'item','search','cloud','restart']:
            command = path_items[1].lower()
            pagename = '/'.join(path_items[2:])
        return (command, pagename)
def render_refs_box(self, req, ids, order = 'year', desc = 1, headhref=False,command=[],page=[] ):
    # Check parameters
    if not ids:
        return []     
    
    fields = self.env.config.get('zotero', 'fields','firstCreator, year, publicationTitle, title' )
    fields = fields.split(',')
    fields = [f.strip() for f in fields]
    labels = self.env.config.get('zotero', 'labels','Authors, Year, Publication, Title' )
    labels = labels.split(',')
    labels = [f.strip() for f in labels]
    
    model = ZoteroModelProvider(self.env)
    
    data = model.get_item_fields(ids,fields, order, desc = desc)
    
    heads = []
    for idx, label in enumerate(labels):
        if headhref and command and page:
            field = fields[idx]
            head = []
            th_class = ''
            th_href = req.href.zotero(command, page, order=field)
            if order == field:
                if desc:
                    th_class = 'desc'
                else:
                    th_class = 'asc'
                    th_href = req.href.zotero(command, page, order=field, desc = str(1))
            head = tag.th(tag.a(labels[idx], href = th_href),class_= th_class)
            heads.append(head)
        else:
            heads.append(tag.th(label))
    body = []
    for idx, item in enumerate(data):
        item_class = 'even'
        if idx % 2 == 1:
            item_class = 'odd'
        item_td = []
        for idx, field in enumerate(fields):
            field_td = []
            if not field or item[idx+1] == 'None':
                field_td = tag.td()
            elif field == 'title':
                field_td = tag.td(tag.a(item[idx+1], 
                    href = req.href.zotero('item',str(item[0]))))
            else:   
                field_td = tag.td(item[idx+1])
            item_td.append(field_td)
        item_tr = tag.tr( item_td,class_=item_class)
        body.append(item_tr)
    return tag.table( tag.thead( heads ), tag.tbody(body),
        class_="listing dirlist", id="dirlist")
def generate_home(self, req):
    
    model = ZoteroModelProvider(self.env)
    
    title = tag.h1( 'Tops' )
    authors_top = model.count_by_author_top()
    authors = []
    for creatorID, firstName, lastName in authors_top:
        authors.append(tag.a( lastName + ' ' + firstName, 
                href = req.href.zotero('search', author = creatorID) ) )
        authors.append(tag.span(' | '))
    authors = tag.tr(tag.th( tag.b('Authors:'), 
        tag.td( authors, 
                tag.a('more...', href = req.href.zotero('cloud', t = 'author' ) ) ),
        valign="top", style="text-align: right; width: 15%;"))
    
    publisher_top = model.count_by_publisher_top()
    publisher = []
    for p in publisher_top:
        publisher.append(tag.a( p, 
                href = req.href.zotero('search', publisher = p) ) )
        publisher.append(tag.br())
    publisher = tag.tr(tag.th( tag.b('Publishers:'), 
            tag.td(publisher, 
                   tag.a('more...', href = req.href.zotero('cloud', t = 'publisher' ))),
            valign="top", style="text-align: right; width: 15%;"))
    
    year_top = model.count_by_year_top()
    years = []
    for y in year_top:
        years.append(tag.a( y, 
                href = req.href.zotero('search', year = y) ) )
        years.append(tag.span(' | '))
    years = tag.tr(tag.th( tag.b('Years:'), 
            tag.td(years, 
                   tag.a('more...', href = req.href.zotero('cloud', t = 'year' ))),
            valign="top", style="text-align: right; width: 15%;"))
    # For recently add
    recent_ids = model.get_recents()
    recents_title = tag.div( tag.br(), tag.br(),tag.h1('Recent Changes'))
    recents = render_refs_box(self, req, recent_ids )
    home = tag.div( title, 
        tag.table(authors, years, publisher, border="0", cellpadding="2", cellspacing="2"),
        recents_title, recents)
    
    return home

def render_cloud(self, req, type, renderer=None ):
    # Codes are from tractags plugin
    min_px = 10.0
    max_px = 30.0
    scale = 1.0
    add_stylesheet(req, 'tags/css/tractags.css')
    
    model = ZoteroModelProvider(self.env)
    value  = []
    labels = []
    links = []
    if type == 'author':
        author_count = model.count_by_author()
        for creatorID, cnum, firstName, lastName in author_count:
            value.append(cnum)
            labels.append(lastName + ' ' + firstName)
            links.append(req.href.zotero('search', author = creatorID))
    if type == 'publisher':
        publisher_count = model.count_by_publisher()
        for publisher, pnum in publisher_count:
            value.append(pnum)
            labels.append(publisher)
            links.append(req.href.zotero('search', publisher = publisher))
    if type == 'year':
        year_count = model.count_by_year()
        for year, ynum in year_count:
            value.append(ynum)
            labels.append(year)
            links.append(req.href.zotero('search', year = year))
    
    
    if renderer is None:
        def default_renderer(label, count, link,percent):
            return tag.a(label, rel='tag', title='%i' % count, href=link,
                             style='font-size: %ipx' %
                                   int(min_px + percent * (max_px - min_px)))
        renderer = default_renderer
    size_lut = dict([(c, float(i)) for i, c in
                     enumerate(sorted(set([r for r in value])))])
    if size_lut:
        scale = 1.0 / len(size_lut)
    ul = tag.ul(class_='tagcloud')
    last = len(value) - 1
    for i, label in enumerate(labels):
        percent = size_lut[value[i]] * scale
        li = builder.li(renderer(label, value[i], links[i], percent))
        if i == last:
            li(class_='last')
        li()
        ul(li, ' ')
    return ul
    return []
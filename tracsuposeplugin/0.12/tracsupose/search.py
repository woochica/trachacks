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
from genshi.builder import tag, Element
import re
import posixpath
import os
import string
from fnmatch import fnmatch

class SupoSENaviContributor(Component):
    implements( INavigationContributor )
    def get_active_navigation_item(self, req):
        if 'REPO_SEARCH' in req.perm:
            return 'reposearch'

    def get_navigation_items(self, req):
        if 'REPO_SEARCH' in req.perm:
            label = "Repo Search"
            yield ('mainnav', 'reposearch',
                   builder.a(label, href=req.href.reposearch()) )

class SupoSERequestHandler(Component):
    implements( ITemplateStreamFilter, IPermissionRequestor, 
        IRequestHandler, ITemplateProvider)
    
    def get_permission_actions(self):
        yield 'REPO_SEARCH'
    def filter_stream(self, req, method, filename, stream, data):
        # Get path
        if filename == 'browser.html':
            # self.req_han = SupoSERequestHandler()
            path = data.get('created_path')
            repo = self.env.get_repository(authname=req.authname)
            node = get_existing_node(req, repo, path, repo.youngest_rev)
            file = ""
            if node:
                if node.isfile:
                    file = posixpath.basename(path)
                    path = posixpath.dirname(path)

            #raise Exception( path )
            filter = Transformer('//div[@id="jumprev"]')
            search = tag.div( tag.form( 
            # tag.div( "Repository search" ),
                tag.input( type = "text", id = "suquery", 
                    name = "q", size = 13, value = ""),
                tag.input( type = "hidden", id = "suquerypath", 
                    name = "p", size = 13, value = path),
                tag.input( type = "hidden", id = "suqueryfile", 
                    name = "f", size = 13, value = file),
                tag.input( type = "submit", value="Repo Search"),
                action=req.href.reposearch(),
                method="get", id="reposearch" ) )
                
            
            return stream | filter.after(search)
        return stream

    

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('supose', resource_filename(__name__, 'htdocs'))]
    def match_request(self, req):
        return req.path_info.startswith('/reposearch')
    def process_request(self, req):
        add_stylesheet(req, 'common/css/trac.css')
        add_stylesheet(req, 'common/css/search.css')
        add_script(req, 'common/js/jquery.js')
        add_script(req, 'common/js/folding.js')
        add_stylesheet(req, 'supose/css/supose.css')
        # raise Exception( path )
        query = req.args.get('q', '')
        path = req.args.get('p', '')
        file = req.args.get('f', '')
        if not path:
            path = "/"
        data = self._prepare_data(req, query, "", "")
        data['path'] = path
        data['file'] = file
        
        to_unicode = Mimeview(self.env).to_unicode
        if query:
            data['quickjump'] = self._check_quickjump(req, query, path)
            if not req.perm.has_permission('REPO_SEARCH'):
                return
            
            supose = self.env.config.get('supose', 'supose' )
            if not supose:
                raise Exception( "supose have to be specified in the section supose of trac.ini" )
            index = self.env.config.get('supose', 'index' )
            if not index:
                raise Exception( "index folder have to be specified in the section supose of trac.ini" )
            
            repo = self.env.get_repository(authname=req.authname)
            
            autoindex = self.config.getbool('supose', 'autoindex')
            if autoindex:
                raise Exception( autoindex )
                indexedrev = BoolOption('supose', 'indexedrev' )
                # Index with SupoSE
                
                youngest = int( repo.youngest_rev )
                #raise Exception( int( indexedrev ) < youngest )
                base = re.search("(svn:.*:)(.*:.*)", repo.get_base() )
                base = base.group(2)
                base = "file:///" +  base
                if not indexedrev:
                    # First Scan
                    first_scan_cmd = supose + " scan --url "
                    first_scan_cmd += base
                    first_scan_cmd += " --create --index "
                    first_scan_cmd += index
                    scan_res = os.popen( first_scan_cmd ).read()
                    indexedrev = youngest
                    self.env.config.set('supose', 'indexedrev',
                               youngest)
                    self.env.config.save()
                    indexedrev = int( indexedrev )
                if int( indexedrev ) < youngest:
                    new_index_cmd = supose + " scan --url "
                    new_index_cmd += base
                    new_index_cmd += " --fromrev " + str( indexedrev )
                    new_index_cmd += " --index " + index
                    scan_res = os.popen( new_index_cmd ).read()
                    # raise Exception( new_index_cmd )
                    self.env.config.set('supose', 'indexedrev',
                               youngest)
                    self.env.config.save()
            # SupoSE search
            supose_cmd = str( supose )
            supose_cmd += " search --fields revision " 
            supose_cmd += "filename path contents --index "
            supose_cmd += index + " --query "
            
            supose_query = "\"" + query + "\""
            if path:
                if path != "/":
                    if path[0] != "/":
                        supose_query += " +path:/"
                    else:
                        supose_query += " +path:"
                    supose_query += path
                    if path[len(path)-1] !="/":
                        supose_query += "/"
                    supose_query += "*"
            if file:
                supose_query += " +filename:"+file
            repo_res = os.popen( supose_cmd + supose_query ).read()
            data['querystring'] = supose_query
            
            
            repo_reg = "(.*[\d]+:[ ]+REVISION:)([\d]+)"
            repo_reg += "( +FILENAME:)(.+)"
            repo_reg += "( +PATH:)(.+)"
            repo_reg += "( +CONTENTS:)"
            
            hits = re.split( repo_reg, repo_res ) 
            # raise Exception( hits )
            spit_len = 8
            rng = range( 1, len(hits), spit_len )
            search_res = tag.div( "testing", id = "reposearch")
            results = []
            for r in rng:
                rev = hits[r+1]
                filename = hits[r+3]
                path = hits[r+5]
                contents = to_unicode( hits[r+7] )
                change = repo.get_changeset(rev)
                href = self.env.href.browser( path + filename ) + "?rev=" + rev
                title = path + filename + "@" + rev
                date = change.date
                author = change.author
                excerpt = shorten_result( contents, query )
                results.extend( self.generate_result( href, 
                        title, date, author, excerpt ) )
            if results:
                    data.update(self._prepare_results(req, "", results))
           
        return 'reposearch.html', data, None        
    def generate_result(self, href, title, date, author, excerpt):
        yield (href, title, date, author, excerpt)
    def _prepare_data(self, req, query, available_filters, filters):
        return {'filters': [{'name': f[0], 'label': f[1],
                             'active': f[0] in filters}
                            for f in available_filters],
                'query': query, 'quickjump': None, 'results': []}
    def _check_quickjump(self, req, kwd,spath):
        """Look for search shortcuts"""
        noquickjump = int(req.args.get('noquickjump', '0'))
        # Source quickjump   FIXME: delegate to ISearchSource.search_quickjump
        quickjump_href = None
        if kwd[0] == '/':
            quickjump_href = req.href.browser(kwd)
            name = kwd
            description = _('Browse repository path %(path)s', path=kwd)
        else:
            link = extract_link(self.env, Context.from_request(req, 'reposearch'),
                                kwd)
            if isinstance(link, Element):
                quickjump_href = link.attrib.get('href')
                name = link.children
                description = link.attrib.get('title', '')
        
        if quickjump_href:
            # Only automatically redirect to local quickjump links
            if not quickjump_href.startswith(req.base_path or '/'):
                noquickjump = True
            if noquickjump:
                return {'href': quickjump_href, 'name': tag.EM(name),
                        'description': description}
            else:
                req.redirect(quickjump_href)
    def _prepare_results(self, req, filters, results):
        page = int(req.args.get('page', '1'))
        results = Paginator(results, page - 1, 100)
        for idx, result in enumerate(results):
            results[idx] = {'href': result[0], 'title': result[1],
                            'date': format_datetime(result[2]),
                            'author': result[3], 'excerpt': result[4]}

        pagedata = []    
        shown_pages = results.get_shown_pages(21)
        for shown_page in shown_pages:
            page_href = req.href.reposearch([(f, 'on') for f in filters],
                                        q=req.args.get('q'),
                                        p=req.args.get('p'),
                                        page=shown_page, noquickjump=1)
            pagedata.append([page_href, None, str(shown_page),
                             'page ' + str(shown_page)])

        fields = ['href', 'class', 'string', 'title']
        results.shown_pages = [dict(zip(fields, p)) for p in pagedata]

        results.current_page = {'href': None, 'class': 'current',
                                'string': str(results.page + 1),
                                'title':None}

        if results.has_next_page:
            next_href = req.href.reposearch(zip(filters, ['on'] * len(filters)),
                                        q=req.args.get('q'), 
                                        p=req.args.get('p'),
                                        page=page + 1,
                                        noquickjump=1)
            add_link(req, 'next', next_href, 'Next Page')

        if results.has_previous_page:
            prev_href = req.href.reposearch(zip(filters, ['on'] * len(filters)),
                                        q=req.args.get('q'), 
                                        p=req.args.get('p'),
                                        page=page - 1,
                                        noquickjump=1)
            add_link(req, 'prev', prev_href, 'Previous Page')

        page_href = req.href.reposearch(
            zip(filters, ['on'] * len(filters)), q=req.args.get('q'),
            p=req.args.get('p'),
            noquickjump=1)
        return {'results': results, 'page_href': page_href}

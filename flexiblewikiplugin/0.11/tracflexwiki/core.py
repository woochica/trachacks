# -*- coding: utf-8 -*-

import re
from genshi.template import TemplateLoader
from trac.core import Component, implements
from trac.web.chrome import ITemplateProvider
from trac.wiki.model import WikiPage

class TracFlexWikiNode:
    """ Page data for wiki structure.
    """
    
    def __init__(self, env, name, req=None):
        """
        """

        # basic: env, name, navpath
        self.env = env
        if name == None or name == '' or name == 'WikiStart':
            self.name = 'WikiStart'
            self.navpath = ''
        else:
            self.name = name
            self.navpath = name        

        # defaults
        self.href = ''
        self.title = self.name
        self.parent = None
        self.children = None
        self.tree = None
        self.weight = 0
        self.hidden = 0        
        
        # get data from request
        self.req = req
        if self.req:
            # get current page
            name = req.args.get('page', '')
            
            # title, hidden, weight, parent for current page node
            if self.name == name or self.navpath == name:
                # title
                self.title = req.args.get('title', self.title)
                # hidden
                self.hidden = req.args.get('hidden', self.hidden) and 1 or 0
                # weight
                try:
                    self.weight = int(req.args.get('weight', self.weight))
                except ValueError:
                    pass
                # parent
                if (not self.isroot) and ('parent' in req.args):
                    self.set_parent_by_name(req.args.get('parent', ''))
            
            # href
            self.href = req.href.wiki(self.navpath)
            # href - strip slash if present
            if (self.href[-1] == '/'):
                self.href = self.href[:-1]

    
    isroot = property(fget=(lambda self: (len(self.navpath) == 0)))
    
    root = property(fget=(lambda self: self._get_root()))
    
    parent_navpath = property(fget=(lambda self: ((not self.parent) and '') or self.parent.navpath))
    
    def set_parent_by_name(self, name):
        if (len(name) > 0) and (self.name == name):
            name = ''
        self.parent = TracFlexWikiNode(self.env, name=name, req=self.req)
        
    def save(self):
        """ Save page node data.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # add empty node if not exists
        try:
            cursor.execute("INSERT INTO flex (name) VALUES (%s)", (self.name,))
            db.commit()
        except:
            db.rollback()
        # update node data
        try:
            cursor.execute("UPDATE flex SET parent=%s,title=%s,weight=%s,hidden=%s WHERE name=%s",
                           (self.parent.navpath, self.title, self.weight, self.hidden, self.name))
            db.commit()
        except:
            db.rollback()
    
    def fetch(self):
        """ Fetch basic data: parent, title, weight
        """
        if not self.parent is None:
            return
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT parent, title, weight, hidden FROM flex WHERE name=%s", (self.name,))
        row = cursor.fetchone()
        parent = ''
        if row and len(row):
            if row[0]:
                parent = row[0]
            self._setup_by_row(row);
        self.set_parent_by_name(parent)
    
    def fetch_children(self, child_fetched):
        """ Fetch children pages.
        """    
        if not self.children is None:
            return
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        #cursor.execute("SELECT name, title, weight FROM flex WHERE parent=%s", (self.navpath,))
        cursor.execute("SELECT name, title, weight, hidden FROM flex \
                        WHERE parent=%s AND hidden=0 ORDER BY weight", (self.navpath,))
        self.children = []
        for row in cursor:
            if (row[0] != self.name):
                if child_fetched and child_fetched.name == row[0]:
                    self.children.append(child_fetched)
                else:
                    node = TracFlexWikiNode(self.env, row[0], self.req)
                    node._setup_by_row(row)
                    node.parent = self
                    self.children.append(node)
    
    def fetch_tree(self):
        """ Fetch all parents-of-parents-of-... up to root.
        """
        if self.tree is not None:
            return
        self.tree = []
        node = self
        child = None
        while True:
            node.fetch()
            node.fetch_children(child)
            if node.parent in self.tree:
                break
            if node.isroot:
                break
            self.tree.insert(0, node.parent)
            child = node
            node = node.parent
        self.tree.append(self)
    
    def _setup_by_row(self, row):
        if (row is None) or (len(row) == 0):
            return
        self.title = row[1]
        self.weight = row[2]
        self.hidden = row[3]
        
    def _get_root(self):
        """ Get root of navigation tree.
        """
        node = self
        while node.parent:
            if node.isroot:
                return node
            node = node.parent
        return node   


class TracFlexWikiComponent(Component):
    """ Base class for components, provides templates.
    """
    implements(ITemplateProvider)
    
    def get_loader(self):
        try:
            return self._loader
        except:
            self._loader = TemplateLoader(self.get_templates_dirs())
        return self._loader
    
    def match_request_prefix(self, req):
        if re.match(r'/flexwiki.*$', req.path_info):
            return 1
    
    def is_wiki_realm(self, req):
        if re.match(r'^/?$', req.path_info) or \
           self.match_request_prefix(req) or \
           re.match(r'/wiki.*$', req.path_info):
            return 1
    
    def is_wiki_edit(self, req, filename = ''):
        if filename == 'wiki_edit.html':
            return True
        if filename == 'wiki_create.html':
            return True
        #if self.is_wiki_realm(req) and (('edit' in req.args) or ('new' in req.args)):
        #    return True
        return False
        
    def is_wiki_view(self, req, filename = ''):
        return (filename == 'wiki_view.html')
    
    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('flexwiki', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
from trac.core import *
from trac.web.api import IRequestFilter
from trac.config import ListOption
from trac.util.html import html
import re

try:
    set = set
except ImportError:
    from sets import Set as set

__all__ = ['NavControlModule']

class NavControlModule(Component):
    """Request filter to hide entries in navigation bars."""

    mainnav = ListOption('navcontrol', 'mainnav',
                              doc='Items to remove from the mainnav bar')

    metanav = ListOption('navcontrol', 'metanav',
                              doc='Items to remove from the metanav bar')

    main2meta = ListOption('navcontrol', 'mainnav_to_metanav',
                              doc='Items to shift from mainnav to metanav bar')
                             
    meta2main = ListOption('navcontrol', 'metanav_to_mainnav',
                              doc='Items to shift from metanav to mainnav bar')
    
    labels = ListOption('navcontrol', 'labels',
                              doc='Labels to assign to navigation items. \
                                   They should be specified as navitem:label e.g \
                                   !wiki:\'My Wiki\',!browser:\'code\'')

    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        self._remove_items(req, 'mainnav')
        self._remove_items(req, 'metanav')    
        self._move_items(req, 'main2meta')
        self._move_items(req, 'meta2main')
        self._relabel_items(req)
        return template, data, content_type

    # Internal methods
    def _remove_items(self, req, name):
        items = set(getattr(self, name))
        prefix_list=['-', '!']
        items |= self._get_items(req, name, prefix_list)
        for item in items:
            navitems = req.chrome['nav'][name]
            for navitem in navitems:
              if navitem['name'] == item:
                navitems.remove(navitem)
        
    def _move_items(self, req, name):
        items = set(getattr(self, name))
        prefix_list=['@', '^']
        if name == 'main2meta':
            nav_from = 'mainnav'
            nav_to   = 'metanav'
        else:
            nav_from = 'metanav'
            nav_to   = 'mainnav'
        items |= self._get_items(req, nav_from, prefix_list)
        #for item in items:
        nav_from_items = req.chrome['nav'][nav_from]
        nav_to_items   = req.chrome['nav'][nav_to]
        for item in items:
            for navitem in nav_from_items:
                if navitem['name'] == item:
                    nav_from_items.remove(navitem)
                    nav_to_items.append(navitem)

    # general helper method
    def _get_items(self, req, name, prefix_list):
      items = set() 
      for item in self.config.get('trac', name, default='').split(','):
        item = item.strip()
        try:
          prefix_list.index(item[0])
          items.add(item[1:])
        except:
          pass
        return items

    def _relabel_items(self, req):
      nvp_dict = {}
      items = set(getattr(self, 'labels'))
      if len(items) > 0:
        for nvp in items:
          try:
            index = nvp.index(':')
            nvp_dict[nvp[0:index].strip()] = nvp[index+1:].strip()
          except:
            pass
        for item in req.chrome['nav']['mainnav'] + req.chrome['nav']['metanav']:
          name = item['name']
          if nvp_dict.has_key(name):
            re_href=re.compile('<a\s+?href="(.*?)"[\s.]*', re.I | re.S | re.M)
            href_val=re_href.findall(item['label'].__str__())
            if len(href_val) > 0:
              item['label'] = html.A(nvp_dict[name], href=href_val[0])



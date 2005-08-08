"""
GeneralLinkSyntax.py
====================

This is plugin module for Trac.
  
Description:

  This is wiki syntax provider to make user defined link as trac link
  style embedding. You can use trac link like 'link:mylink:123'
  which is rendered as anchor to user defined URL with parameter.

  This syntax is mainly developed to make link to mailing-list
  archive. For example, 'link:dev:123' means 'link to archived message
  having X-Ml-Count: is 123' and it will be expanded like this:
  <a href='http://www.some-where.org/archive/dev/123'>dev:123</a>

  See this page for more detail.
  http://trac-hacks.swapoff.org/wiki/GeneralLinkSyntaxPlugin

Author:

  Shun-ichi Goto <gotoh@taiyo.co.jp>

"""
import re
from trac.core import *
from trac.util import escape
from trac.wiki import IWikiSyntaxProvider


class GeneralLinkSyntaxProvider(Component):
    implements(IWikiSyntaxProvider)

    # config file syntax:
    # [xxxx]
    # module=xxx
    # names=name1,name2,name3,...
    # exposed_names=name1,...
    # name1_url=url
    # name1_disp=url
    # name2_url=url2
    # ...
   
    # _link_info is hash of name to (dispname, url)
    _link_info = {}
    # _expose_names are string array to be exposed
    _exposed_names = []
    
    _common_ns = 'link'
    _config_section = 'link'
    _disp_suffix = '_disp'
    _url_suffix = '_url'

    def __init__(self):
        self._load_config()

    # utilities
    def _get_config(self, name, default=None):
        return self.config.get(self._config_section, name, default)
    
    def _load_config(self):
        self._link_info = {}
        self._exposed_names = []
        names = self._get_config('names', '').split(',')
        if len(names) == 0:
            return                      # no entry
        for name in names:
            disp = self._get_config(name + self._disp_suffix, name)
            url = self._get_config(name + self._url_suffix)
            if not url:
                raise Exception("No URL defined for '%s'" % name)
            self.log.debug('Adding link: %s = (%s, %s)' % (name, disp, url))
            self._link_info[name] = (disp, url)
        names = self._get_config('exposed_names')
        if names:
            self._exposed_names = [name.strip() for name in names.split(',')]

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        ret = [(self._common_ns, self._format_link)]
        if self._exposed_names:
            for name in self._exposed_names:
                ret.append((name, self._format_exposed_link))
        return ret

    def get_wiki_syntax(self):
        return []

    def _format_exposed_link(self, formatter, ns, target, label):
        # normalize with common ns, "name:id" => "link:name:id"
        if target == label:
            label = ns + ':' + target
        target = ns + ':' + target
        return self._format_link(formatter, self._common_ns, target, label)
    
    def _format_link(self, formatter, ns, target, label):
        # target may:
        #   link:name, link:name:13
        # or with exposed name:
        #   name, name:123

        items = target.split(':')
        id = None
        name = None
        if 1 == len(items):
            # wihtout id
            name, id = items[0], ""
        elif 2 == len(items):
            name, id = items
        else:
            return "<span style='color:red'>[invalid link: %s]</span>" % \
                       (ns + ':' + target)
        
        if not name or not self._link_info.has_key(name):
            return "<span style='color:red'>[Unknown link name: '%s']</span>" \
                   % name
        disp = self._link_info[name][0]
        if label == target or label == ns + ':' + target:
            # label is not specifed in wiki text, (ex. [link:name])
            try:
                label = disp % id
            except:
                label = disp + ":" + id
        url = self._link_info[name][1]
        try:
            url = url % id
        except:
            pass
        return '<a href="%s">%s</a>' % (url, label)


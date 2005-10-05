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
from trac.util import TracError
from trac.util import escape
from trac.wiki import IWikiSyntaxProvider

from model import LinkInfo

class GeneralLinkSyntaxProvider(Component):
    """Provides 'link:' syntax which is expanded to user defined links.
    """
    implements(IWikiSyntaxProvider)

    # config file syntax:
    # [xxxx]
    # module=xxx
    # names=name1,name2,name3,...
    # expose=name1,...
    # name1_url=url
    # name1_disp=url
    # name2_url=url2
    # ...
   
    # _links is hash of name to LinkInfo
    _links = {}
    
    _common_ns = 'link'
    _config_section = 'link'
    _disp_suffix = '_disp'
    _url_suffix = '_url'

    # private config operations
    def _get_config(self, key, default=None):
        return self.config.get(self._config_section, key, default)

    def _set_config(self, key, value):
        self.config.set(self._config_section, key, value)

    def _remove_config(self, key):
        self.config.remove(self._config_section, key)
    
    # private util

    def _change_link(self, name, expose, disp, url):
        # validate
        if not name:
            raise TracError('name must be specified.')
        # delete?
        if expose == None:
            info = self._links.pop(name)
            # clean config
            self._remove_config(info.name + '_disp')
            self._remove_config(info.name + '_url')
        else:
            # new object with error check
            info = LinkInfo(name, expose, disp, url)
            self._links[name] = info
            self._set_config(info.name + '_disp', info.disp)
            self._set_config(info.name + '_url', info.url)

        # update 'names' and 'expose'
        names = [n for n in self._links]
        expose = [n for n in names if self._links[n].expose]
        self._set_config('names', ', '.join(names))
        self._set_config('expose', ', '.join(expose))
        self.config.save()
        self.log.debug('config is updated.')
    

    # API
    
    def load(self):
        self._links = {}
        exposes = {}
        for name in self._get_config('expose').split(','):
            name = name.strip()
            if name == '':
                continue
            exposes[name] = True
            
        for name in self._get_config('names', '').split(','):
            name = name.strip()
            if name == '':
                continue
            disp = self._get_config(name + self._disp_suffix, name)
            url = self._get_config(name + self._url_suffix)
            if not url:
                raise TracError("No URL defined for '%s'" % name)
            expose = exposes.has_key(name)
            try:
                self._internal_add(LinkInfo(name, expose, disp, url))
            except TracError, e:
                self.log.debug('LinkInfo Error: ' + str(e))

    def get_links(self):
        """Return sorted link info"""
        names = [n for n in self._links]
        names.sort()
        return [self._links[n] for n in names]

    def get_link(self, name):
        if self._links.has_key(name):
            return self._links[name]
        else:
            None

    def has_name(self, name):
        return self._links.has_key(name)

    def _internal_add(self, info):
        if self._links.has_key(info.name):
            raise TracError('Already exist: ' + info.name)
        #self.log.debug('Adding link: %s = (%s, %s, %s)' % \
        #               (info.name, info.expose, info.disp, info.url))
        self._links[info.name] = info;

    def add(self, name, expose, disp, url):
        # validate
        if self._links.has_key(name):
            raise TracError("Link is already exist: '%s'" % name)
        self.log.debug('adding ' + name)
        self._change_link(name, expose, disp, url)

    def delete(self, name):
        if not self._links.has_key(name):
            raise TracError("Link is not exist: '%s'" % name)
        self.log.debug('deleting ' + name)
        self._change_link(name, None, None, None)

    def modify(self, name, expose, disp, url):
        if not self._links.has_key(name):
            raise TracError("Link is not exist: '%s'" % name)
        self.log.debug('modifying ' + name)
        self._change_link(name, expose, disp, url)
    
    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        self.load()
        ret = [(self._common_ns, self._format_link)]
        for name in [x.name for x in self._links.values() if x.expose]:
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
            name, id = items[0], ''
            trailer = ''
        elif 2 <= len(items):
            name, id = items
            trailer = ':'.join(items[2:])

        # if name not found, leave all as is
        if not name or not self._links.has_key(name):
            self.log.debug("Unknown link name: '%s'" % name)
            return ':'.join(items)
        
        info = self._links[name]
        disp = info.disp
        if label == target or label == ns + ':' + target:
            # label is not specifed in wiki text, (ex. [link:name])
            try:
                label = disp % id
            except:
                label = disp + ':' + id
        url = info.url
        try:
            url = url % id
        except:
            pass
        return '<a href="%s">%s</a>%s' % (url, label, trailer)


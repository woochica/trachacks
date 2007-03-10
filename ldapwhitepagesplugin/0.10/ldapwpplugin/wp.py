# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Herbert Valerio Riedel <hvr@gnu.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from trac.core import *

#from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
#from trac.util import escape
from trac.util.html import html, Markup, escape

from trac.web import HTTPNotFound, RequestDone, IRequestHandler
from trac.web.chrome import ITemplateProvider, INavigationContributor

from trac.wiki import WikiSystem, IWikiSyntaxProvider
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_oneliner, wiki_to_html

import datetime
import time
import os
import sys
import re
import ldap

class LdapWpPlugin(Component):
    implements(IRequestHandler,ITemplateProvider,IWikiSyntaxProvider,IWikiMacroProvider)

    def __init__(self):
	c = lambda x, d: self.config.get('ldap-wp', x, d)
	self._ldap_uri = c('ldap_uri', 'ldap://localhost')
        self._user_rdn = c('ldap_user_rdn', '')
	self._user_filter = c('ldap_user_filter', 'objectclass=posixAccount')
        #self._ldap = ldap.initialize(self._ldap_uri)
        self._ldap = ldap.ldapobject.ReconnectLDAPObject(self._ldap_uri)
	self._jpegPhoto_placeholder = c('jpegPhoto_placeholder', None)
	self._jpegPhoto_width = c('jpegPhoto_width', None)

    def get_uids(self):
	try:
        	r=self._ldap.search_s(self._user_rdn, ldap.SCOPE_ONELEVEL, self._user_filter, ['uid'])
 		return [i['uid'][0] for dn,i in r]
	except:
		return []

    def get_realname(self, uid):
        try:
            [(dn,data)]=self._ldap.search_s(self._user_rdn, ldap.SCOPE_ONELEVEL, "uid="+uid, ['sn','givenName'])
            return "%s %s" % (data['givenName'][0],data['sn'][0])
        except:
            return None

    def get_jpegPhoto(self, uid):
        try:
            [(dn,data)]=self._ldap.search_s(self._user_rdn, ldap.SCOPE_ONELEVEL, "uid="+uid, ['jpegPhoto'])
            return data['jpegPhoto'][0]
        except:
            return open(self._jpegPhoto_placeholder).read()

    def get_info(self, uid):
        try:
            [(dn,data)]=self._ldap.search_s(self._user_rdn, ldap.SCOPE_ONELEVEL, "uid="+uid)
            return data
        except:
            return None

    # IWikiMacroProvider
    def get_macros(self):
        yield 'FaceImg'

    def _render_macro_FaceImg(self, req, content):
        uid=content
        rn=self.get_realname(uid)
        if not rn:
            raise Exception("unknown user")
	if self._jpegPhoto_width:
        	return Markup(html.IMG(src=req.href.user("%s/jpegPhoto" % uid), alt=rn, width=self._jpegPhoto_width))
	return Markup(html.IMG(src=req.href.user("%s/jpegPhoto" % uid), alt=rn))

    def render_macro(self, req, name, content):
        if name=='FaceImg':
            return self._render_macro_FaceImg(req,content)
        raise Exception("macro name '%s' not recognized" % name)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return []
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        yield ('user', self._format_link)

    def get_wiki_syntax(self): # cb(formatter, ns, match)
        yield (r"(?<![A-Za-z])(%s)(?![A-Za-z])" % ("|".join(self.get_uids())), self._format_link2)

    def _format_link(self, formatter, ns, params, label):
        return html.a(label, href=formatter.href.user(params), title=self.get_realname(params))

    def _format_link2(self, formatter, ns, match):
        return self._format_link(formatter, 'user', ns, ns)

    # IRequestHandler methods
    def match_request(self, req):
        return (req.path_info+'/').startswith('/user/')

    def process_request(self, req):
        if req.path_info+'/'=='/user/':
            qs = ''
        else:
            [qs]=req.path_info.split('/user/',1)[1:]

        qs=[item for item in qs.split('/') if len(item)>0]

        content=u""

        if len(qs)==0:
            content += u"= User Whitepages List =\n[[BR]]\n"

            r=self._ldap.search_s(self._user_rdn, ldap.SCOPE_ONELEVEL, "objectclass=posixAccount", ['uid','sn','givenName'])

            r=[(data['uid'][0],data['sn'][0],data['givenName'][0]) for dn,data in r]
            r.sort()

            content += u"|| `uid` || '''given name''' || '''surname''' ||\n" 
            for uid,sn,gn in r:
                content += u"|| %s || %s || %s ||\n" % (uid,gn,sn)
            
            req.hdf['wp.text'] = wiki_to_html(content, self.env, req)
            req.hdf['title'] = u'Whitepages List'
            return 'wp.cs', 'text/html'
        elif len(qs)==1:
            uid=qs[0]

            data=self.get_info(uid)
            if not data:
                raise HTTPNotFound("uid %s not found" % uid)

            content += (u'= Whitepages Entry for %s =\n' % uid)

            content += u'''{{{
#!html
<table style="border: none; padding: 15px; margin: 0px">
<tr><td style="vertical-align: top">
}}}
'''

            if True or ('jpegPhoto' in data):
                content += (u'[[FaceImg(%s)]]\n' % uid)
                content += u'''{{{
#!html
</td><td style="vertical-align: top; width: 40px;">&nbsp;</td><td style="vertical-align: top">
}}}
'''
            content += (u'== %s, %s ==\n' % (data['sn'][0],data['givenName'][0]))
            content += (u" '''Username''':: %s[[BR]]\n" % uid)
            if 'mail' in data:
                content += (u" '''Email''':: [mailto:%s %s][[BR]]\n" % (data['mail'][0],data['mail'][0]))
            if 'telephoneNumber' in data:
                content += (u" '''Phone''':: %s[[BR]]\n" % data['telephoneNumber'][0])
            if 'birthDate' in data:
                birthDate=data['birthDate'][0]
                bday=datetime.date(*time.strptime(birthDate, "%Y-%m-%d")[0:3])
                tday=datetime.date.today()
                age = tday.year-bday.year
                ofs = (tday-datetime.date(tday.year,bday.month,bday.day)).days
                if ofs<0:
                    days=(datetime.date(tday.year,bday.month,bday.day)-datetime.date(tday.year-1,bday.month,bday.day)).days
                else:
                    days=(datetime.date(tday.year+1,bday.month,bday.day)-datetime.date(tday.year,bday.month,bday.day)).days
                age = float(age)+(float(ofs)/float(days))
                    
                content += (u" '''Age''':: %.2f years[[BR]]\n" % age)
                content += (u" '''Birthdate''':: %s[[BR]]\n" % birthDate)

            content += u'''{{{
#!html
</td></tr>            
</table>
}}}
'''
            
            req.hdf['wp.text'] = wiki_to_html(content, self.env, req)
            req.hdf['title'] = (u'Whitepages Entry for %s' % uid)
            return 'wp.cs', 'text/html'
            
        elif len(qs)==2:
            uid=qs[0]
            if qs[1]=='jpegPhoto':
                jpegPhoto = self.get_jpegPhoto(uid)
                if jpegPhoto:
                    req.send_response(200)
                    req.send_header('Content-Type', 'image/jpeg')
                    req.send_header('Content-Length', len(jpegPhoto))
                    req.end_headers()

                    if req.method != 'HEAD':
                        req.write(jpegPhoto)
                    raise RequestDone
                
            
        raise HTTPNotFound("File not found")

# -*- coding: utf-8 -*-


# Copyright 2004 Matthew Good
# "THE BEER-WARE LICENSE" (Revision 42):
# Matthew Good <matt-good.net> wrote this file.  As long as you retain
# this notice you can do whatever you want with this stuff. If we meet some
# day, and you think this stuff is worth it, you can buy me a beer in return.
# Matthew Good

# BEER-WARE LICENSE courtesy of Poul-Henning Kamp <phk@login.dknet.dk>

# Author Matthew Good <trac@matt-good.net>
# ported to trac 0.11 by <friends.of.neo@gmail.com>

# Trac WikiMacro for rendering links to Javadoc urls
# Accepts one or two arguments separated by a comma.

# The first argument is the fully qualified Java class or package.
# Classes are assumed to begin with an uppercase letter and packages
# with a lowercase letter according to standard Java naming conventions.

# The second optional argument is the link text.
# If the second argument is ommitted the class name is used,
# or in the case of a package the full package name is used.

#-------------------------------------------------------------------------------
# This block can be edited to change the urls used for the Javadocs
# Note: all Javadoc urls should end with a '/' or index.html

j2se_url = 'http://java.sun.com/j2se/1.4.2/docs/api/index.html'
j2ee_url = 'http://java.sun.com/j2ee/1.4/docs/api/index.html'
xerces_url = 'http://xml.apache.org/xerces2-j/javadocs/api/index.html'
commons_logging_url = 'http://commons.apache.org/logging/commons-logging-1.0.3/docs/api/index.html'
commons_beanutils_url = 'http://commons.apache.org/beanutils/commons-beanutils-1.6.1/docs/api/'
commons_collections_url = 'http://commons.apache.org/collections/api-2.1.1/index.html'
commons_lang_url = 'http://commons.apache.org/lang/api-1.0.1/index.html'

urls = {
    # The URL for the standard Java API
    '': j2se_url,

    # Mappings from package names to Javadoc URLs
    'javax.activation': j2ee_url,
    'javax.ejb': j2ee_url,
    'javax.enterprise': j2ee_url,
    'javax.jms': j2ee_url,
    'javax.mail': j2ee_url,
    'javax.management': j2ee_url,
    'javax.resource': j2ee_url,
    'javax.security.jacc': j2ee_url,
    'javax.servlet': j2ee_url,
    'javax.transaction': j2ee_url,
    'javax.xml': j2ee_url,
    
    'org.apache.commons.logging': commons_logging_url,
    'org.apache.commmons.beanutils': commons_beanutils_url,
    
    'org.apache.commons.collections':  commons_collections_url,
    'org.apache.commons.lang':   commons_lang_url,

    'org.w3c.dom': xerces_url,
    'org.xml.sax': xerces_url
    }
#-------------------------------------------------------------------------------
from trac.core import *
from urlparse import urljoin
from string import ascii_uppercase
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase

revison = "$Rev$"
url = "$URL$"

class javadocMacro(WikiMacroBase):

	def best_match(self, value, items):
		match = ''
		for i in items:
			if len(i) > len(match) and value.startswith(i):
				match = i

		return match

	def base_url(self, package):
		return urls[self.best_match(package, urls.keys())]
    
	def package_path(self, package):
		return package.replace('.', '/') + '/'
    
	def type_path(self, package, clss):
		return self.package_path(package) + (clss and (clss + '.html') or 'package-summary.html')
    
	def javadoc_url(self, package, clss):
		return urljoin(self.base_url(package), self.type_path(package, clss))
    
	def split_at(self, a, index):
		return (a[:index], a[index + 1:])
    
	def split_type(self, value):
		package, clss = self.split_at(value, value.rfind('.'))
		if clss[0] in ascii_uppercase:
			return (package, clss)
		else:
			return (value, None)
    
	def link(self, href, text):
		return '<a href="%s" class="javadoc">%s</a>' % (href, text)
    
	def javadoc_link(self, value, linktext):
		package, clss = self.split_type(value)
		return self.link(self.javadoc_url(package, clss), linktext or clss or package)

	def expand_macro(self, formatter, name, args):
		txt = args.split(',', 1)
		javatype = txt[0]
		linktext = len(txt) > 1 and txt[1].strip() or None
		return self.javadoc_link(javatype, linktext)
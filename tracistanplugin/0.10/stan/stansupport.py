# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@asylumware.com>

import sys
import os
import os.path
import time
import datetime

from StringIO import StringIO
from pkg_resources import resource_filename

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, Chrome
from trac.web.api import RequestDone

from nevow.flat import flatten, ten
from nevow import rend
from nevow import tags as T

try:
    import tidy
except ImportError:
    tidy = False

__all__ = ['TracIStan']
__version__ = '0.1'

class StanEngine:

    def _inherits_tag (self, template, locals, globals):
        self.__superTemplate = eval(file(os.path.join(self.basedir, template),
                                         'rU' ).read(), locals, globals)
        return T.invisible

    def _replace_tag (self, slot):
        return T.invisible(slot=slot)

    def _include_tag (self, template, locals, globals):
        try:
            return eval(file(os.path.join(self.basedir, template), 'rU').read(),
                        locals, globals)
        except:
            print "ERROR IN INCLUDE", template
            raise

    def find_template (self, template):
        """Find the location of the template amongst the template dirs

        """
        filename = template
        try:
            template_dirs = self.template_dirs
        except KeyError:
            template_dirs = []
        for dir in template_dirs:
            absolute_path = os.path.join(dir, filename)
            if os.path.exists(absolute_path):
                return absolute_path
            continue
        return filename

    def render(self, info, format="html", fragment=False, template=None):
        """Renders the template to a string using the provided info.

        info: dict of variables to pass into template
        format: can only be "html" at this point
        template: path to template

        """
        self.__superTemplate = None

        filename = self.find_template(template)
        self.basedir = os.path.dirname(filename)

        ns = {}

        if format.startswith('tidy.'):
            pretty, format = format.split('.')
        else:
            pretty = False
        if format == 'html':
            ns.update(__import__('nevow.tags', ns, ns, ['__all__']).__dict__)
            ns.update(__import__('nevow.entities', ns, ns, 
                                 ['__all__']).__dict__)
        else: # import user-defined Stan tags
            ns.update(__import__('%s.tags' % format, ns, ns, 
                                 ['__all__']).__dict__)

        ns['vars'] = self.Vars(info)
#        if self.get_extra_vars:
#            ns['std'] = self.get_extra_vars (  ) [ 'std' ]
        ns['render'] = rend
        ns['inherits'] = lambda template: self._inherits_tag(template, ns, ns)
        ns['replace'] = ns ['override'] = self._replace_tag
        ns['include'] = lambda template: self._include_tag(template, ns, ns)
        ns['formerror' ] = T.Proto('form:error')

        try:
            self.__template = eval(file(filename, 'rU').read(), ns, ns)
        except:
            print "ERROR IN TEMPLATE", filename
            raise

        if self.__superTemplate:
            parts = dict([ (c.attributes['slot'], flatten(c.children))
                           for c in self.__template.children])
            for slot, fragment in parts.items():
                self.__superTemplate.fillSlots(slot, fragment)
            output = flatten(self.__superTemplate)
        else:
            output = flatten(self.__template)

        if pretty and tidy:
            options = dict ( input_xml = True,
                             output_xhtml = True,
                             add_xml_decl = False,
                             doctype = 'omit',
                             indent = 'auto',
                             tidy_mark = False )
            return str(tidy.parseString(output, **options))

        return output

    class Vars:
        """Turn a dict into a class for notational convenience in templates.

        """
        def __init__(self, values):
            self.__dict__.update(values)


class TracIStan(Component):
    """Interface for using the Stan templating language

    To use Stan for templates instead of ClearSilver, simply subclass this
    class.  It implements the IRequestHandler and ITemplateProvider interfaces.
    
    Instead of returning a template name and content_type, the return line
    should look like:

    return self._return(req, 'templatename.stan', 'content_type')

    As usual, if content_type is ommitted, then text/html is assumed.
    
    """
    abstract = True
#    implements(IRequestHandler, ITemplateProvider)
    implements(IRequestHandler)
    stantheman = StanEngine()

    # IRequestHandler methods
    def match_request(self, req):
        return NotImplementedError

    def process_request(self, req):
        return NotImplementedError

    def _return(self, req, template, content_type='text/html'):
        """ Wrap the return so that things are processed by Stan
    
        """
        hdf = getattr(req, 'hdf', None)
        if hdf:
            req.standata.update(self._convert_hdf_to_data(hdf))

        if req.args.has_key('hdfdump'):
            # FIXME: the administrator should probably be able to disable HDF
            #        dumps
            from pprint import PrettyPrinter
            pp = PrettyPrinter
            outstream = StringIO()
            pp.pprint(req.standata, outstream)
            content_type = 'text/plain'
            data = outstream.getvalue()
            outstream.close()
        else:
            data = self._render(req.standata, template)
         
        req.send_response(200)
        req.send_header('Cache-control', 'must-revalidate')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', content_type + ';charset=utf-8')
        req.send_header('Content-Length', len(data))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(data)
        raise RequestDone

    def _render(self, data, template):
        c = Chrome(self.env)
        self.stantheman.template_dirs = c.get_all_templates_dirs()
        return self.stantheman.render(data, template=template)

    def _convert_hdf_to_data(self, hdf):
        """Converts an HDFWrapper to a dictionary

        """
        def reformat_data(data):
            """Check to see if the keys are sequential numbers and reformats 
               into a list

            """
            try:
                keys = [int(k) for k in data.keys()]
                keys.sort()
                datalist = [data[str(k)] for k in keys]
                return datalist
            except ValueError:
                return data

        def hdf_tree_walk(node):
            d = {}
            while node:
                name = node.name() or ''
                value = node.value()
                if (value or not node.child()) and name:
                    d[name] = value.strip()
                if node.child() and name:
                    data = hdf_tree_walk(node.child())
                    data = reformat_data(data)
                    if data:
                        d[name] = data
                node = node.next()
            return d

        return hdf_tree_walk(hdf.hdf.child())

# I don't think I need this
#    # ITemplateProvider
#    def get_templates_dirs(self):
#        return NotImplemented Error
#        return [resource_filename(__name__, 'templates')]
#
#    def get_htdocs_dirs(self):
#        raise NotImplementedError



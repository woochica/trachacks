#!/usr/bin/python

'''
DoapView

Trac macro to convert DOAP (Description of a Project) RDF files to HTML in a wiki page

Example:

    [[DoapView(doap.rdf)]] 

'''

import os

from genshi.template import TemplateLoader
from trac.wiki.macros import WikiMacroBase
from trac.attachment import Attachment
from rdflib import Namespace

from doapfiend.doaplib import load_graph

FOAF = Namespace("http://xmlns.com/foaf/0.1/")

def get_templates_dir():
    return os.path.join(os.path.dirname(__file__), 'templates')

LOADER = TemplateLoader(
    get_templates_dir(),
    auto_reload=True
)


class DoapViewMacro(WikiMacroBase):

    '''
    Embed a DOAP file as HTML in wiki-formatted text. The only argument is 
    the filename. The filename is the name of a file attachment on the 
    current page.


    '''

    def expand_macro(self, formatter, name, content):
        if not content:
            return ''
        attachment = formatter.resource.child('attachment', content)
        realm = formatter.resource.realm
        resource_id = formatter.resource.id   
        rdf_path = Attachment(self.env, realm, resource_id, content).path

        page = open(rdf_path, 'r').read()
        doap = load_graph(page)
        tmpl = LOADER.load('doap.html')

        return tmpl.generate(
                name= doap.name,
                doap=doap,
                foaf=FOAF
                    ).render('html', doctype='html')


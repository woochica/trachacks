# -*- coding: utf-8 -*-

import base64
import hashlib
import os
import pickle
import re
from datetime import datetime
from subprocess import Popen, PIPE

from trac.core import *
from trac.config import Option
from trac.web import IRequestHandler, RequestDone
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html, system_message
from trac.wiki.macros import WikiMacroBase

__all__ = ["PlantUMLMacro", "PlantUMLRenderer"]

class PlantUMLMacro(WikiMacroBase):
    """
    A macro to include a PlantUML Diagrams
    """
    
    implements(IRequestHandler)

    plantuml_jar = Option("plantuml", "plantuml_jar", "", "Path to PlantUML .jar file")
    java_bin = Option("plantuml", "java_bin", "java", "Path to the Java binary file") 

    def expand_macro(self, formatter, name, content):
        if content is None:
            return system_message("No UML text defined!")
        if not self.plantuml_jar:
            return system_message("plantuml_jar option not defined in .ini")
        if not os.path.exists(self.plantuml_jar):
            return system_message("plantuml.jar not found: %s" % self.plantuml_jar)

        args, _ = parse_args(content)
        source = args[0].encode('utf-8').strip()

        try:
            graphs = pickle.loads(base64.b64decode(formatter.req.session.get('plantuml',"")))
        except:
            graphs = {}
            
        img_id = hashlib.sha1(source).hexdigest()            
            
        #Clean old images
        for key, graph in graphs.items():
            if (datetime.now() - graph[1]).seconds > 3600:
                del graphs[key]              

        if not graphs.has_key(img_id):
            
            cmd = "%s -jar -Djava.awt.headless=true \"%s\" -charset UTF-8 -pipe" % (self.java_bin, self.plantuml_jar)
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            (stdout, stderr) = p.communicate(input=source)
            if p.returncode != 0:
                return system_message("Error running plantuml: %s" % stderr)

            graphs[img_id] = (stdout, datetime.now())
        
        formatter.req.session['plantuml'] = base64.b64encode(pickle.dumps(graphs))

        out = "{{{\n#!html\n<img src='%s' alt='PlantUML Diagram' />\n}}}\n" % formatter.href("plantuml", id=img_id)
        return format_to_html(self.env, formatter.context, out)

    # IRequestHandler
    def match_request(self, req):
        return re.match(r'/plantuml?$', req.path_info)
    
    def process_request(self, req):
        graphs = pickle.loads(base64.b64decode(req.session.get('plantuml', None)))
        
        img, tstamp = graphs[req.args.get('id')]

        #file = req.args.get('file', None)
        #tfile = open(file, "rb")
        req.send(img, 'image/png', status=200)
        #tfile.close()
        #os.unlink(file)
        return ""
        #raise RequestDone

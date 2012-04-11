# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Polar Technologies - www.polartech.es
# Copyright (C) 2010 Alvaro J Iradier
# Copyright (C) 2012 Ryan J Ollos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import hashlib
import os
import re
from subprocess import Popen, PIPE

from genshi.builder import tag
from trac.config import Option
from trac.core import implements
from trac.util.translation import _
from trac.web import IRequestHandler
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html, system_message
from trac.wiki.macros import WikiMacroBase

__all__ = ["PlantUMLMacro"]

img_dir = 'cache/plantuml'

class PlantUMLMacro(WikiMacroBase):
    """
    A macro to include a PlantUML Diagrams
    {{{
    #!PlantUML
    @startuml
    Alice -> Bob: Authentication Request
    Bob --> Alice: Authentication Response
    Alice -> Bob: Another authentication Request
    Alice <-- Bob: another authentication Response
    @enduml
    }}}
    """

    implements(IRequestHandler)

    plantuml_jar = Option('plantuml', 'plantuml_jar', '', 'Path to PlantUML .jar file')
    java_bin = Option('plantuml', 'java_bin', 'java', 'Path to the Java binary file')
    
    def __init__(self):
        self.abs_img_dir = os.path.join(os.path.abspath(self.env.path), img_dir)
        if not os.path.isdir(self.abs_img_dir):
            os.makedirs(self.abs_img_dir)

    def expand_macro(self, formatter, name, content):
        if not content:
            return system_message("No UML text defined!")
        if not self.plantuml_jar:
            return system_message("Installation error: plantuml_jar option not defined in trac.ini")
        if not os.path.exists(self.plantuml_jar):
            return system_message("Installation error: plantuml.jar not found: %s" % self.plantuml_jar)

        args, _ = parse_args(content)
        markup = args[0].encode('utf-8').strip()
        img_id = hashlib.sha1(markup).hexdigest()

        if not self._is_img_existing(img_id):
            cmd = "%s -jar -Djava.awt.headless=true \"%s\" -charset UTF-8 -pipe" % (self.java_bin, self.plantuml_jar)
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            (img_data, stderr) = p.communicate(input=markup)
            if p.returncode != 0:
                return system_message("Error running plantuml: %s" % stderr)            
            self._write_img_to_file(img_id, img_data)
        
        link = formatter.href('plantuml', id=img_id)
        return tag.img(src=link)

    # IRequestHandler
    def match_request(self, req):
        return re.match(r'/plantuml?$', req.path_info)
    
    def process_request(self, req):
        img_id = req.args.get('id')
        img_data = self._read_img_from_file(img_id)
        req.send(img_data, 'image/png', status=200)
        return ""

    # Internal
    def _get_img_path(self, img_id):
        img_path = os.path.join(self.abs_img_dir, img_id)
        img_path += '.png'
        return img_path

    def _is_img_existing(self, img_id):
        img_path = self._get_img_path(img_id)
        return os.path.isfile(img_path)

    def _write_img_to_file(self, img_id, data):
        img_path = self._get_img_path(img_id)
        open(img_path, 'wb').write(data)

    def _read_img_from_file(self, img_id):
        img_path = self._get_img_path(img_id)
        img_data = open(img_path, 'rb').read()
        return img_data

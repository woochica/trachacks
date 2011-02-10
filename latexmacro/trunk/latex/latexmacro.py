# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Authors: Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
#          Vivien Lacourba <vivien.lacourba@ercim.org>
#
# Based on trac2latex http://trac-hacks.org/wiki/Trac2LatexPlugin
#      and latex-math https://labs.truelite.it/packages/wiki/TrueliteTracUtils
#
# Requirements: trac 0.11, latex, dvipng
#               trac2latex's LatexMacro must be disabled

from trac.wiki.macros import WikiMacroBase

import os, tempfile, md5, glob

# Include your favourite LaTeX preamble
tex_preamble = r'''
\documentclass{article} 
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\pagestyle{empty} 
\begin{document}
\begin{equation*}
'''
tex_end = r'''
\end{equation*}
\end{document}
'''

class LatexMacro(WikiMacroBase):
    r"""Latex WikiProcessor:
    Now you can specify small pieces of latex code into any wiki context, like WikiHtml.
    
    Ex.:
    {{{
       {{{
       #!Latex
       \frac{\alpha^{\beta^2}}{\delta + \alpha}
       }}}
    }}}
    This code will produce a PNG file, inserted directly in the body of the Wiki page.
    """
    def expand_macro(self, formatter, name, content):
       if not content:
           return ''

       filename = md5.new(content).hexdigest()
       images_url = formatter.href.chrome('site', '/latex-images')
       images_folder = os.path.join(os.path.normpath(self.env.get_htdocs_dir()), 'latex-images')

       if not os.path.exists(images_folder):
           os.mkdir(images_folder)
       
       if not os.access('%s/%s.png' % (images_folder, filename), os.F_OK):
           tmpdir = tempfile.mkdtemp(prefix="latexmacro")
           fn = tmpdir + "/macro"

           f = open(fn + ".tex", 'w+')
           f.write(tex_preamble)
           f.write(content)
           f.write(tex_end)
           f.close()
           
           # compile LaTeX document. A DVI file is created
           ret = os.system('latex -output-directory %s -interaction nonstopmode %s >/dev/null 2>/dev/null' % (tmpdir, fn + ".tex"))
           cmd = "dvipng -T tight -x 1200 -z 6 -bg Transparent " \
                 + "-o %s/%s.png %s 2>/dev/null 1>/dev/null" \
                 % (images_folder, filename, fn)
           ret = os.system(cmd)   
       
           self.clean_tmp_dir(tmpdir)

       return '<img src="%s/%s.png"/></a>' % (images_url, filename)

    def clean_tmp_dir(self, tmpdir):
        for f in glob.glob(os.path.join(tmpdir ,"*")):
            os.unlink(f)
        os.rmdir(tmpdir)

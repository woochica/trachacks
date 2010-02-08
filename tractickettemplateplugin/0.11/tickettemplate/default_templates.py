# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         default_templates.py
# Purpose:      The ticket template Trac plugin default templates module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

DEFAULT_TEMPLATES = [
("defect", """= bug description =

= bug analysis =

= fix recommendation ="""),
("enhancement", """= problem =

= analysis =

= enhancement recommendation ="""),
("task", """= phenomenon =

= background analysis =

= implementation recommendation ="""),
("default", """= phenomenon =

= reason =

= recommendation ="""),
                     ]
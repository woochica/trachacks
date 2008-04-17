# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         default_templates.py
# Purpose:      The ticket template Trac plugin default templates module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


DEFAULT_TEMPLATES = [
("defect", """= 缺陷描述 =

= 缺陷分析 =

= 修订建议 ="""),
("enhancement", """= 不如意 =

= 分析 =

= 增进建议 ="""),
("task", """= 问题现象 =

= 背景分析 =

= 实施建议 ="""),
("default", """= 现象 =

= 思考 =

= 建议 ="""),
                     ]
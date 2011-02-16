# -*- coding: utf-8 -*-
"""
This macro allows you to add anchor.

Author: Dmitri Khijniak

Usage:
{{{
  [[Anchor(anchor_name,text )]]
}}}
or
{{{
  [[Anchor(anchor_name)]]
}}}
Where: 
anchor_name::
  is a URL used to reference the anchor
text::
  visible text describing the anchor

Example:
{{{
  [[Anchor(anchor)]]
  [[Anchor(anchor, name)]]
}}}
"""

def execute(hdf, args, env):
    args = tuple(args.split(","))
    print args
    if len(args) == 2:
      return '<a name="%s" href="#%s">%s</a>' % (args[0],args[0],args[1])
    else:
      return '<a name="%s"></a>' % args

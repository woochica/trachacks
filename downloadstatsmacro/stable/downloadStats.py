##########################################################################
#
# downloadStats.py: macro for Trac to show webalizer stats
#
# Download Stats receive a pattern and show the sum of all matched in
# webalizer html files
# See http://
#
# ====================================================================
# Copyright (c) 2005 Debian-BR-CDD Team.  All rights reserved.
#
#   This package is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 dated June, 1991.
#
#   This package is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this package; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#   02111-1307, USA.
#
#########################################################################
# Authors: Tiago Bortoletto Vaz <tiago@debian-ba.org>
# 	   Otavio Salvador <otavio@debian.org>

import re
import os

def uniq(alist):    # Fastest without order preserving
    set = {}
    map(set.__setitem__, alist, [])
    return set.keys()

def getHitsFromFile(file,pattern,webalizer_path):
    """
    in: a html webalizer file, a pattern and the webalizer path
    out: a list of hits, one item for each match
    """
    pattern = pattern or 'http'
    file=open(webalizer_path+file,'r')
    current=file.read()
    avaliable=re.findall(r""">
<TD ALIGN=right><FONT SIZE="-1"><B>[0-9]+</B></FONT></TD>
<TD ALIGN=right><FONT SIZE="-2">[0-9]+,[0-9]+%</FONT></TD>
<TD ALIGN=right><FONT SIZE="-1"><B>[0-9]+</B></FONT></TD>
<TD ALIGN=right><FONT SIZE="-2">[0-9]+,[0-9]+%</FONT></TD>
<TD ALIGN=left NOWRAP><FONT SIZE="-1"><A HREF="http://.*</A></FONT></TD></TR>
<TR>
""",current)
    file.close()
    hits=[]
    for file in uniq(avaliable): 
        if pattern in file:
            hits_tmp=re.findall(r"<B>[0-9]+</B>",file)[0]
	    hits.append(int(re.sub(r'[^0-9]','',hits_tmp)))
    return hits

def getHitsFromAll(args):
    """
    in: a string to be split using '|' as delimiter where the first argument is the webalizer path,
    other are pattern that should be matched. Ex. /var/www/webalizer|file.iso|file2.raw
    out: the sum of all matched patterns
    """
    arg=args.split('|')
    webalizer_path=arg.pop(0)
    patterns=arg
    all_hits=0
    file_pattern=r".html" #FIXME: build a true pattern for usage_xxx.html, not every .html
    all_files=os.listdir(webalizer_path)
    for file in all_files:
        if file_pattern in file:
            for pattern in patterns:
		for i in getHitsFromFile(file,pattern,webalizer_path):
		    all_hits+=i
    return all_hits

def execute(hdf,args,env):
    return str(getHitsFromAll(args))

# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#

import SVGdraw as SVG
import os
import md5

from colorsys import rgb_to_hsv, hsv_to_rgb
from math import sqrt
from random import randrange, seed
from revtree.api import *
from trac.core import *
from trac.web.href import Href

__all__ = ['SvgColor', 'SvgGroup', 'SvgOperation', 'SvgRevtree']

UNIT = 25
SQRT2=sqrt(2)
SQRT3=sqrt(3)

# Debug functions to place debug circles on the SVG graph
debugw = []
def dbgPt(x,y,c='red',d=5):
    debugw.append(SVG.circle(x,y,d, 'white', c, '2'))
def dbgLn(x1,y1,x2,y2,c='red',w=3):
    debugw.append(SVG.line(x1,y1,x2,y2,c,w))
def dbgDump(svg):
    map(svg.addElement, debugw)
    
def textwidth(text):
    # kludge, this should get the actual font parameters, etc...
    length = text and len(text) or 0
    return (1+length)*(UNIT/2.5)

class SvgColor(object):
    """Helpers for color management (conversion, generation, ...)"""
    
    colormap = { 'black':       (0,0,0),
                 'white':       (0xff,0xff,0xff),
                 'darkred':     (0x7f,0,0),
                 'darkgreen':   (0,0x7f,0),
                 'darkblue':    (0,0,0x7f),
                 'red':         (0xdf,0,0),
                 'green':       (0,0xdf,0),
                 'blue':        (0,0,0xdf),
                 'gray':        (0x7f,0x7f,0x7f),
                 'orange':      (0xff,0x9f,0) }
    
    def __init__(self, value=None, name=None):
        if value is not None:
            if isinstance(value, SvgColor):
                self._color = value._color
            elif isinstance(value, unicode):
                self._color = SvgColor.str2col(value.encode('ascii'))
            elif isinstance(value, str):
                self._color = SvgColor.str2col(value)
            elif isinstance(value, tuple):
                if len(value) != 3:
                    raise AssertionError, "invalid color values"
                self._color = value
            else:
                raise AssertionError, "unsupportedcolor: %s" % value
        elif name is not None:
            self._color = SvgColor.from_name(name)
        else:
            self._color = SvgColor.random()
            
    def __str__(self):
        return "#%02x%02x%02x" % self._color
        
    def rgb(self):
        return "rgb(%d,%d,%d)" % self._color

    def set(self, string):
        self._color = SvgColor.str2col(string)
        
    def str2col(string):
        if string.startswith('#'):
            string = string[1:]
            if len(string) == 6:
                r = int(string[0:2], 16)
                g = int(string[2:4], 16)
                b = int(string[4:6], 16)
                return (r,g,b)
            elif len(string) == 3:
                r = int(string[0:1], 16)*16
                g = int(string[1:2], 16)*16
                b = int(string[2:3], 16)*16
                return (r,g,b)
            else:
                raise AssertionError, "invalid color"
        else:
            if SvgColor.colormap.has_key(string):
                return SvgColor.colormap[string]
            else:
                raise AssertionError, "unknown color: %s" % string
    str2col = staticmethod(str2col)

    def random():
        rand = "%03d" % randrange(1000)
        return (128+14*int(rand[0]), 
                128+14*int(rand[1]), 
                128+14*int(rand[2]))
    random = staticmethod(random)
    
    def from_name(name):
        dig = md5.new(name.encode('utf-8')).digest()
        vr = 14*(int(ord(dig[0]))%10)
        vg = 14*(int(ord(dig[1]))%10)
        vb = 14*(int(ord(dig[2]))%10)
        return (128+vr, 128+vg, 128+vb)
    from_name = staticmethod(from_name)
    
    def invert(self):
        self._color = (0xff-self._color[0],
                       0xff-self._color[1],
                       0xff-self._color[2])

    def strongify(self):
        (r,g,b) = (float(self._color[0])/0xff, 
                   float(self._color[1])/0xff, 
                   float(self._color[2])/0xff)
        (h,s,v) = rgb_to_hsv(r,g,b)
        v /= 1.5;
        s *= 3.0;
        if s > 1: s = 1
        (r,g,b) = hsv_to_rgb(h,s,v)
        return SvgColor((int(r*0xff),int(g*0xff),int(b*0xff)))

    def lighten(self):
        (r,g,b) = (float(self._color[0])/0xff, 
                   float(self._color[1])/0xff, 
                   float(self._color[2])/0xff)
        (h,s,v) = rgb_to_hsv(r,g,b)
        v *= 1.5;
        if v > 1: v = 1
        (r,g,b) = hsv_to_rgb(h,s,v)
        return SvgColor((int(r*0xff),int(g*0xff),int(b*0xff)))


class SvgBaseChangeset(object):
    """Base class for graphical changeset/revision nodes
       This changeset cannot be rendered in the SVG graph"""
    
    def __init__(self, parent, revision, position=None):
        self._parent = parent
        self._revision = revision
        self._position = position
        self._htw = textwidth(str(self._revision))/2
        self._radius = self._htw + UNIT/6
        self._extent = (2*self._radius,2*self._radius)

    def __cmp__(self, other):
        return cmp(self._revision, other._revision)

    def build(self):
        if self._position is None:
            self._position = self._parent.get_slot(self._revision)
                           
    def extent(self):
        return self._extent 
        
    def branch(self):
        return self._parent
        
    def visible(self):
        return False
                              
    def position(self, anchor=''):
        (x,y) = self._position
        fo = self._radius
        ho = SQRT2*fo/2
        h = len(anchor) > 1
        if 'n' in anchor:
            y -= (h and ho or fo);
        if 's' in anchor:
            y += (h and ho or fo);
        if 'w' in anchor:
            x -= (h and ho or fo);
        if 'e' in anchor:
            x += (h and ho or fo);
        return (x,y)

    def render(self):
        pass


class SvgChangeset(SvgBaseChangeset):
    """Changeset/revision node"""
    
    def __init__(self, parent, changeset):
        SvgBaseChangeset.__init__(self, parent, changeset.rev)
        self._shape = 'circle'
        self._enhance = False
        self._tag_offset = 0
        self._fillcolor = self._parent.fillcolor()
        self._strokecolor = self._parent.strokecolor()
        self._textcolor = SvgColor('black')
        self._classes = ['svgchangeset']
        
    def set_shape(self, shape):
        """Define the shape of the svg changeset [circle,square,hexa].
           If the first letter is uppercase, the shape is augmented with
           fancy lines.
        """
        self._shape = shape.lower()
        self._enhance = shape[0] != self._shape[0]
        
    def mark_first(self):
        """Marks the changeset as the first of the branch.
           Inverts the background and the foreground color"""
        self._classes.append('firstchangeset')
        
    def mark_last(self):
        """Mark the changeset as the latest of the branch"""
        self._classes.append('lastchangeset')

    def build(self):
        SvgBaseChangeset.build(self)
        (fgc, bgc) = (self._strokecolor, self._fillcolor)
        txc = self._textcolor
        if 'firstchangeset' in self._classes:
            (fgc, bgc) = (bgc, fgc)
        if 'lastchangeset' in self._classes:
            bgc = SvgColor('black')
            txc = SvgColor('white')
            
        widgets = []
        if self._shape == 'circle':
            widgets.append(SVG.circle(self._position[0], self._position[1],
                                      self._radius, bgc, fgc,
                                      self._parent.strokewidth()))
            if self._enhance:
                (x,y) = self._position
                (d,hr) = (self._radius*SQRT3/2, self._radius/2)
                widgets.append(SVG.line(x-d,y-hr,x+d,y-hr, 
                                        fgc, self._parent.strokewidth()))
                widgets.append(SVG.line(x-d,y+hr,x+d,y+hr, 
                                        fgc, self._parent.strokewidth()))
                              
        elif self._shape == 'square':
            r = UNIT/6
            size = self._radius-r
            widgets.append(SVG.rect(self._position[0]-size, 
                                    self._position[1]-size,
                                    2*size, 2*size, bgc, fgc,
                                    self._parent.strokewidth()))
            outline.attributes['rx'] = r
            outline.attributes['ry'] = r        
            
        elif self._shape == 'hexa':
            (x,y) = self._position
            (r,hr) = (self._radius, self._radius/2)
            pd = SVG.pathdata()
            pd.move(x,y-r)
            pd.line(x+r,y-hr)
            pd.line(x+r,y+hr)
            pd.line(x,y+r)
            pd.line(x-r,y+hr)
            pd.line(x-r,y-hr)
            pd.line(x,y-r)
            widgets.append(SVG.path(pd, bgc, fgc, 
                                    self._parent.strokewidth()))
        else:
            raise AssertionError, \
                  "unsupported changeset shape (%d)" % self._revision
        title = SVG.text(self._position[0], 
                         self._position[1] + UNIT/6,
                         str(self._revision), 
                         self._parent.fontsize(), self._parent.fontname())
        title.attributes['style'] = 'fill:%s; text-anchor: middle' % txc.rgb()
        widgets.append(title)
        g = SVG.group('grp%d' % self._revision, elements=widgets)
        link = "%s/changeset/%d" % (self._parent.urlbase(), self._revision)
        self._link = SVG.link(link, elements=[g])
        if self._revision:
            self._link.attributes['style'] = \
                'color: %s; background-color: %s' % \
                    (self._strokecolor, self._fillcolor)
            self._link.attributes['id'] = 'rev%d' % self._revision
            self._link.attributes['class'] = ' '.join(self._classes)
                    
    def tag_offset(self, height):
        offset = self._tag_offset
        self._tag_offset += height
        return offset

    def strokewidth(self):
        return self._parent.strokewidth()

    def strokecolor(self):
        return self._parent.strokecolor()
    
    def fillcolor(self):
        return self._parent.fillcolor()
        
    def fontsize(self):
        return self._parent.fontsize()
        
    def fontname(self):
        return self._parent.fontname()

    def urlbase(self):
        return self._parent.urlbase()
        
    def visible(self):
        return True
               
    def render(self):
        self._parent.svg().addElement(self._link)


class SvgBranchHeader(object):
    """Branch title"""
    
    def __init__(self, parent, path, title, lastrev):
        self._parent = parent
        self._title = title or ''
        self._path = path
        self._rev = lastrev
        self._tw = textwidth(self._title)+UNIT/2
        self._w = max(self._tw, 6*UNIT)
        self._h = 2*UNIT
        
    def position(self, anchor=''):
        (x,y) = (self._position[0]+self._w/2, self._position[1]) 
        if 'n' in anchor:
            pass;
        if 's' in anchor:
            y += self._h;
        if 'w' in anchor:
            pass;
        if 'e' in anchor:
            x += self._w;
        return (x,y)
        
    def extent(self):
        return (self._w, self._h)
        
    def build(self):
        self._position = self._parent.position()
        x = self._position[0]+(self._w-self._tw)/2
        y = self._position[1]
        r = UNIT/2
        rect = SVG.rect(x,y,self._tw,self._h,
                        self._parent.fillcolor(), 
                        self._parent.strokecolor(), 
                        self._parent.strokewidth())
        rect.attributes['rx'] = r
        rect.attributes['ry'] = r        
        text = SVG.text(self._position[0]++self._w/2, 
                        self._position[1]+self._h/2+UNIT/6,
                        self._title.encode('utf-8'), 
                        self._parent.fontsize(), self._parent.fontname())
        text.attributes['style'] = 'text-anchor: middle'
        name = self._title.encode('utf-8').replace('/','')
        g = SVG.group('grp%s' % name, elements=[rect, text])
        href = Href(self._parent.urlbase())
        self._link = SVG.link(href.browser(self._path, rev='%d' % self._rev), 
                              elements=[g])
        
    def render(self):
        self._parent.svg().addElement(self._link)
        

class SvgTag(object):
    """Graphical view of a tag"""
    
    def __init__(self, parent, path, title, rev, src):
        self._parent = parent
        self._title = title or ''
        self._path = path
        self._revision = rev
        self._srcchgset = src
        self._tw = textwidth(self._title)+UNIT/2
        self._w = self._tw
        self._h = 1.2*UNIT
        self._opacity = 75
        
    def position(self, anchor=''):
        (x,y) = (self._position[0]+self._w/2, self._position[1]) 
        if 'n' in anchor:
            pass;
        if 's' in anchor:
            y += self._h;
        if 'w' in anchor:
            pass;
        if 'e' in anchor:
            x += self._w;
        return (x,y)
        
    def extent(self):
        return (self._w, self._h)
        
    def build(self):
        (sx, sy) = self._srcchgset.position()
        h_offset = self._srcchgset.tag_offset(self._h)
        self._position = (sx + (self._srcchgset.extent()[0])/2,
                          sy - (3*self._h)/2 + h_offset)
        x = self._position[0]+(self._w-self._tw)/2
        y = self._position[1]
        r = UNIT/2
        rect = SVG.rect(x,y,self._tw,self._h,
                        self._srcchgset.strokecolor(),
                        self._srcchgset.fillcolor(), 
                        self._srcchgset.strokewidth())
        rect.attributes['rx'] = r
        rect.attributes['ry'] = r        
        rect.attributes['opacity'] = str(self._opacity/100.0) 
        text = SVG.text(self._position[0]+self._w/2, 
                        self._position[1]+self._h/2+UNIT/4,
                        "%s" % self._title.encode('utf-8'), 
                        self._srcchgset.fontsize(), 
                        self._srcchgset.fontname())
        txc = SvgColor('white')
        text.attributes['style'] = 'fill:%s; text-anchor: middle' % txc.rgb()
        name = self._title.encode('utf-8').replace('/','')
        g = SVG.group('grp%d' % self._revision, elements=[rect, text])
        link = "%s/changeset/%d" % (self._parent.urlbase(), self._revision)
        self._link = SVG.link(link, elements=[g])
        self._link.attributes['id'] = 'rev%d' % self._revision
        self._link.attributes['style'] = \
            'color: %s; background-color: %s' % \
                (self._srcchgset.fillcolor(), self._srcchgset.strokecolor())
        
    def render(self):
        self._parent.svg().addElement(self._link)


class SvgBranch(object):
    """Branch (set of changesets which whose commits share a common base
       directory)"""
       
    def __init__(self, parent, branch, style):
        self._parent = parent
        self._branch = branch
        self._svgchangesets = {}
        self._svgtags = {}
        self._svgwidgets = [[] for l in IRevtreeEnhancer.ZLEVELS]
        self._maxchgextent = [0,0]
        self._fillcolor = self._get_color(branch.name, parent.trunks)
        self._strokecolor = self._fillcolor.strongify()
        self._source = branch.source()
        try:
            self.get_slot = self.__getattribute__('get_%s_slot' % style)
        except AttributeError:
            raise AssertionError, "Unsupported branch style: %s" % style
        pw = None
        transitions = []
        changesets = branch.changesets(parent.revrange);
        changesets.sort()
        changesets.reverse()
        if changesets[0].last:
            # it would require parsing the history another time to find
            # the previous changeset when it is not in the specified range
            lastrev = changesets[len(changesets) > 1 and 1 or 0].rev
        else:
            lastrev = changesets[0].rev
        self._svgheader = \
            SvgBranchHeader(self, branch.name, branch.prettyname, lastrev)
        for c in changesets:
            svgc = SvgChangeset(self, c)
            self._update_chg_extent(svgc.extent())
            if pw is None:
                transitions.append(SvgAxis(self, self._svgheader, svgc))
            else:
                transitions.append(SvgTransition(self, pw, svgc, 'gray'))
            self._svgchangesets[c] = svgc
            self._svgwidgets[IRevtreeEnhancer.ZMID].append(svgc)
            pw = svgc
        svgc = SvgBaseChangeset(self, 0)
        self._update_chg_extent(svgc.extent())
        self._svgchangesets[0] = svgc
        self._svgwidgets[IRevtreeEnhancer.ZMID].append(svgc)
        self._svgwidgets[IRevtreeEnhancer.ZMID].extend(transitions)
        
    def __cmp__(self, other):
        xs = self._position[0]+self._extent[0]
        os = other._position[0]+other._extent[0]
        return cmp(xs,os)
        
    def _update_chg_extent(self, extent):
        if self._maxchgextent[0] < extent[0]:
            self._maxchgextent[0] = extent[0]
        if self._maxchgextent[1] < extent[1]:
            self._maxchgextent[1] = extent[1]
            
    def _get_color(self, name, trunks):
        """Creates a random pastel color based on the branch name 
        or returns a predefined color if the branch is a trunk"""
        if name in trunks:
            return SvgColor(self._parent.env.config.get('revtree', 
                                                        'trunkcolor', 
                                                        '#cfcfcf'))
        else:
            return SvgColor(name=name)

    def create_tag(self, tag):
        svgcs = self.svgchangeset(tag.source())
        self._svgwidgets[IRevtreeEnhancer.ZFORE].append(\
            SvgTag(self, tag.name, tag.prettyname, tag.rev, svgcs))
                      
    def build(self, position):
        self._position = position
        self._slot = self._slotgen()
        self._svgheader.build()
        (w, h) = self._svgheader.extent()
        for wl in self._svgwidgets:
            for wdgt in wl:
                if not isinstance(wdgt, SvgTag):
                    wdgt.build()
                    h += wdgt.extent()[1]
                else: 
                    wdgt.build()
                    (tw, th) = wdgt.extent()
                    nw = tw/2 + wdgt.position()[0]-position[0]
                    if nw > w: w = nw 
        self._extent = (w, h)
            
    def svgarrow(self, color, head):
        return self._parent.svgarrow(color, head)
    
    def header(self):
        return self._svgheader
        
    def svgchangesets(self):
        return self._svgchangesets.values()
                
    def svgchangeset(self, changeset):
        if self._svgchangesets.has_key(changeset):
            return self._svgchangesets[changeset]
        return None
        
    def branch(self):
        return self._branch
        
    def position(self):
        return self._position
        
    def extent(self):
        return self._extent
        
    def get_compact_slot(self, revision):
        return self._slot.next()
    
    def get_timeline_slot(self, revision):
        x = self.vaxis()
        if revision != 0:
            y = self._parent.chgoffset(revision)
            y = (2+y)*2*self._maxchgextent[1]
        else:
            changesets = []
            for (k,v) in self._svgchangesets.items():
                if v._revision != 0:
                    changesets.append(k)
            changesets.sort()
            oldest = changesets[0]
            y = self._svgchangesets[oldest].position()[1]
            y += 2*self._maxchgextent[1]
        return (x,y)
            
    def strokewidth(self):
        return self._parent.strokewidth()

    def strokecolor(self):
        return self._strokecolor
    
    def fillcolor(self):
        return self._fillcolor
        
    def fontsize(self):
        return self._parent.fontsize
        
    def fontname(self):
        return self._parent.fontname

    def urlbase(self):
        return self._parent.urlbase()
        
    def _slotgen(self):
        x = self._position[0] + self._svgheader.extent()[0]/2
        y = self._position[1] + self._svgheader.extent()[1] + \
            2*self._maxchgextent[1]
        while True:
            yield (x,y)
            y += 2*self._maxchgextent[1]
            
    def vaxis(self):
        """Return the position of the vertical axis"""
        return self._position[0] + self._svgheader.extent()[0]/2
            
    def svg(self):
        return self._parent.svg()

    def render(self, level=None):
        self._svgheader.render()
        if level:
            map(lambda w: w.render(), self._svgwidgets[level])
        else:
            for wl in self._svgwidgets:
                map(lambda w: w.render(), wl)


class SvgAxis(object):
    """Simple graphical line between a header and the youngest
       revision of a branch"""
       
    def __init__(self, parent, head, tail, color='#7f7f7f'):
        self._parent = parent
        self._head = head
        self._tail = tail
        self._color = SvgColor(color)

    def build(self):
        sp = self._head.position('s')
        dp = self._tail.position('n')
        self._extent = (abs(dp[0]-sp[0]),abs(dp[1]-sp[1]))
        self._widget = SVG.line(sp[0], sp[1], dp[0], dp[1], self._color, 
                                self._parent.strokewidth())
        self._widget.attributes['stroke-dasharray']='4,4'

    def extent(self):
        return self._extent

    def render(self):
        self._parent.svg().addElement(self._widget)


class SvgTransition(object):
    """Simple graphical line between two consecutive changesets 
       on the same branch"""
       
    def __init__(self, parent, srcChg, dstChg, color):
        self._parent = parent
        self._source = srcChg
        self._dest = dstChg
        self._color = color

    def build(self):
        sp = self._dest.position('n')
        dp = self._source.position('s')
        self._extent = (abs(dp[0]-sp[0]),abs(dp[1]-sp[1]))
        self._widget = SVG.line(sp[0], sp[1], dp[0], dp[1], self._color, 
                                self._parent.strokewidth())
        self._widget.attributes['marker-end'] = \
            self._parent.svgarrow(self._color, False)

    def extent(self):
        return self._extent

    def render(self):
        self._parent.svg().addElement(self._widget)


class SvgGroup(object):
    """Graphical group of consecutive changesets within a same branch"""
    
    def __init__(self, parent, firstChg, lastChg, 
                 color='#fffbdb', opacity=50):
        self._parent = parent
        self._first = firstChg
        self._last  = lastChg
        self._fillcolor = SvgColor(color)
        self._strokecolor = self._fillcolor.strongify()
        self._opacity = opacity
    
    def build(self):
        spos = self._first.position()[1]
        epos = self._last.position()[1]
        if spos > epos:
            (self._first, self._last) = (self._last, self._first)
        sp = self._first.position('n')
        ep = self._last.position('s')
        r = UNIT/2
        w = self._first.extent()[0] + UNIT
        h = ep[1] - sp[1] + UNIT
        x = sp[0] - w/2
        y = sp[1] - UNIT/2
        self._widget = SVG.rect(x,y,w,h,
                                self._fillcolor, 
                                self._strokecolor, 
                                self._parent.strokewidth())
        self._widget.attributes['rx'] = r 
        self._widget.attributes['ry'] = r 
        self._widget.attributes['opacity'] = str(self._opacity/100.0) 
        self._extent = (w,h)
        
    def extent(self):
        return self._extent

    def render(self):
        self._parent.svg().addElement(self._widget)
        
        
class SvgOperation(object):
    """Graphical operation between two changesets of distinct branches 
       (such as a switch/branch creation, a merge operation, ...)"""
       
    def __init__(self, parent, srcChg, dstChg, color='black', classes=[]):
        self._parent = parent
        self._source = srcChg
        self._dest = dstChg
        self._color = SvgColor(color)
        self._classes = classes

    def build(self):
        if self._source.branch() == self._dest.branch():
            self._widget = None
            self._parent.env.log.warn("Invalid operation")
            return 
        # get the position of the changeset to tie
        (xs,ys) = self._source.position()
        (xe,ye) = self._dest.position()
        # swap start and end points so that xs < xe
        if xs > xe:
            head = True
            (self._source, self._dest) = (self._dest, self._source)
            (xs,ys) = self._source.position()
            (xe,ye) = self._dest.position()
        else:
            head = False
        xbranches = self._parent.xsvgbranches(self._source, self._dest)        
        # find which points on the changeset widget are used for connections
        if xs < xe:
            ss = 'e'
            se = 'w'
        else:
            ss = 'w'
            se = 'e'
        ps = self._source.position(ss)
        pe = self._dest.position(se)
        # compute the straight line from start to end widgets
        a = (ye-ys)/(xe-xs)
        b = ys-(a*xs)
        bz = []
        # compute the points through which the 'operation' curve should go 
        (xct,yct) = (ps[0],ps[1])
        points = [(xct,yct)]
        for br in xbranches:
            x = br.vaxis()
            y = (a*x)+b
            ycu = ycd = None
            schangesets = br.svgchangesets()
            schangesets.sort()
            # add an invisible changeset in place of the branch header to avoid
            # special case for the first changeset
            hpos = br.header().position()
            hchg = SvgBaseChangeset(br, 0, (hpos[0], hpos[1]+3*UNIT/2))
            schangesets.append(hchg)
            schangesets.reverse()
            pc = None
            for c in schangesets:
                # find the changesets which are right above and under the 
                # selected point, and store their vertical position
                yc = c.position()[1]
                if yc < y:
                    ycu = yc
                if yc >= y:
                    ycd = yc
                    if not ycu:
                        if pc:
                            ycu = pc.position()[1]
                        elif c != schangesets[-1]:
                            ycu = schangesets[-1].position()[1]
                    break
                pc = c
            if not ycu or not ycd:
                pass
                # in this case, we need to create a virtual point (TODO)
            else:
                xt = x
                yt = (ycu+ycd)/2
                if a != 0:
                    a2 = -1/a
                    b2 = yt - a2*xt
                    xl = (b2-b)/(a-a2)
                    yl = a2*xl + b2
                    nx = xt-xl
                    ny = yt-yl
                    dist = sqrt(nx*nx+ny*ny)
                    radius = (3*c.extent()[1])/2
                    add_point = dist < radius
                else:
                    add_point = True
                # do not insert a point if the ideal curve is far enough from
                # an existing changeset
                if add_point:
                    # update the vertical position for the bezier control 
                    # point with the point that stands between both closest 
                    # changesets
                    (xt,yt) = self._parent.fixup_point((xt,yt))
                    points.append((xt,yt))
        if head:
            points.append(pe)
        else:
            points.append((pe[0]-UNIT,pe[1]))
        # now compute the qbezier curve
        pd = SVG.pathdata()
        pd.move(points[0][0],points[0][1])
        if head:
            pd.line(points[0][0]+UNIT,points[0][1])
        for i in range(len(points)-1):
            (xl,yl) = points[i]
            (xr,yr) = points[i+1]
            (xi,yi) = ((xl+xr)/2,(yl+yr)/2)
            pd.qbezier(xl+2*UNIT,yl,xi,yi)
            pd.qbezier(xr-2*UNIT,yr,xr,yr)
        if not head:
            pd.line(pe[0],pe[1])
        self._widget = SVG.path(pd, 'none', self._color, 
                                self._parent.strokewidth())
        self._widget.attributes['marker-%s' % (head and 'start' or 'end') ] = \
            self._parent.svgarrow(self._color, head)
        if self._classes:
            self._widget.attributes['class'] = ' '.join(self._classes)

    def extent(self):
        return self._extent

    def render(self):
        if self._widget:
            self._parent.svg().addElement(self._widget)
        

class SvgArrows(object):
    """Arrow headers for graphical links and operations"""
    
    def __init__(self, parent):
        self._parent = parent
        self._markers = {}
        
    def _get_name(self, color, head):
        fcolor = str(color)
        if fcolor.startswith('#'):
            fcolor = fcolor[1:]
        return 'arrow_%s_%s' % (head and 'head' or 'tail', fcolor)
        
    def create(self, color, head):
        name = self._get_name(color, head)
        if not self._markers.has_key(name):
            # It seems that WebKit needs some adjustements ...
            # xos = (3.0*UNIT/100)
            # yos = (3.0*UNIT/100)
            # ... but Gecko does not
            xos = 0
            yos = 0
            if head:
                marker = SVG.marker(name, (0,0,10,8), 0, 4, UNIT/4, UNIT/4,
                                    fill=SvgColor(color), orient='auto')
                marker.addElement(SVG.polyline(((0-xos,4-yos),(10-xos,0-yos),
                                                (10-xos,8-yos),(0-xos,4-yos))))
            else:
                marker = SVG.marker(name, (0,0,10,8), 10, 4, UNIT/4, UNIT/4,
                                    fill=SvgColor(color), orient='auto')
                marker.addElement(SVG.polyline(((0+xos,0-yos),(0+xos,8-yos),
                                                (10+xos,4-yos),(0+xos,0-yos))))
            self._markers[name] = marker
        return name
        
    def build(self):
        pass
        
    def render(self):
        map(self._parent.svg().addElement, self._markers.values())

    
class SvgRevtree(object):
    """Main object that represents the revision tree as a SVG graph"""

    def __init__(self, env, repos, urlbase, enhancers, optimizer):
        """Construct a new SVG revision tree"""
        # Environment
        self.env = env
        # URL base of the repository
        self.url_base = urlbase
        # Repository instance
        self.repos = repos
        # Range of revision to process
        self.revrange = None
        # Optional enhancers
        self.enhancers = enhancers
        # Optimizer
        self.optimizer = optimizer
        # Trunk branches
        self.trunks = self.env.config.get('revtree', 'trunks', 
                                          'trunk').split(' ')
        # FIXME: Use CSS properties instead - when browsers support them...
        # Font name
        self.fontname = self.env.config.get('revtree', 'fontname', 'arial')
        # Font size
        self.fontsize = self.env.config.get('revtree', 'fontsize', '14pt')
        # Dictionary of branch widgets (branches as keys)
        self._svgbranches = {}
        # Markers
        self._arrows = SvgArrows(self)
        # List of inter branch operations
        self._svgoperations = []
        # List of changeset groups
        self._svggroups = []
        # Operation points
        self._oppoints = {}
        # Add-on elements (from enhancers)
        self._addons = []
        # Init color generator with a predefined value
        seed(0)
                
    def position(self):
        """Return the position of the revision tree widget"""
        return (UNIT,2*UNIT)
        
    def extent(self):
        """Return the extent of the revtree"""
        return (int(self._extent[0]),int(self._extent[1]))
        
    def strokewidth(self):
        """Return the width of a stroke"""
        return 3
        
    def svgbranch(self, rev=None, branchname=None, branch=None):
        """Return a branch widget, based on the revision number or the 
           branch id"""
        if not branch:
            if rev:
                chg = self.repos.changeset(rev)
                if not chg:
                    self.env.log.warn("No changeset %d" % rev)
                    return None
                self.env.log.info("Changeset %d, branch %s" % (rev, chg.branchname))
                branch = self.repos.branch(chg.branchname)
            elif branchname:
                branch = self.repos.branch(branchname)
        if not branch:  
            return None
        if not self._svgbranches.has_key(branch):
            return None
        return self._svgbranches[branch]
        
    def svgbranches(self):
        return self._svgbranches
        
    def svgarrow(self, color, head):
        return 'url(#%s)' % self._arrows.create(color, head)
        
    def create(self, req, revisions=None, branches=None, authors=None, 
                     hidetermbranch=False, style='compact'):
        if revisions is not None:
            self.revrange = revisions
        else:
            self.revrange = self.repos.revision_range()
        if hidetermbranch:
            allbranches = filter(lambda b: b.is_active(self.revrange), 
                                 self.repos.branches().values())
        else:
            allbranches = self.repos.branches().values()
        revisions = []
        for b in allbranches:
            if branches:
                if b.name not in branches:
                    continue
            if authors:
                if not [a for a in authors for x in b.authors() if a == x]:
                    continue
            svgbranch = SvgBranch(self, b, style)
            self._svgbranches[b] = svgbranch
            revisions.extend([c.rev for c in b.changesets()])
        revisions.sort()
        revisions.reverse()
        self._vtimes = {}
        vtime = 0
        for r in revisions:
            self._vtimes[r] = vtime
            vtime += 1
        for enhancer in self.enhancers:
            self._addons.append(enhancer.create(self.env, req, 
                                                self.repos, self))
        for tag in self.repos.tags().values():
            self.env.log.info("Found tag: %r" % tag.name)
            if tag.clone:
                svgbr = self.svgbranch(rev=tag.clone[0])
                if svgbr:
                    svgbr.create_tag(tag)
                     
    def build(self):
        """Build the graph"""
        branches = self.optimizer.optimize(self.repos, \
            [svgbr.branch() for svgbr in self._svgbranches.values()])
        branch_xpos = UNIT
        svgbranches = [self.svgbranch(branch=b) for b in branches]
        for svgbranch in svgbranches:
            svgbranch.build((branch_xpos, UNIT/6))
            #branch_xpos += svgbranch.header().extent()[0] + UNIT
            branch_xpos += svgbranch.extent()[0] + UNIT
        # TODO: discard tags for which source changeset do not exist 
        #for svgtag in self.svgtags().values():
        #    self.env.log.info("Build Tag %s" % svgtag)
        #    svgtag.build()
        map(lambda e: e.build(), self._addons)
        # FIXME: why not using svgbranches ?
        svgbranches = self._svgbranches.values()
        svgbranches.sort()
        maxheight = 0
        for b in svgbranches:
            h = b.extent()[1]
            if h > maxheight:
                maxheight = h
        if not svgbranches:
            raise EmptyRangeError
        w = svgbranches[-1].position()[0] - svgbranches[0].position()[0] + \
            svgbranches[-1].extent()[0] + 2*UNIT
        maxheight += UNIT 
        self._extent = (w,maxheight)
            
    def urlbase(self):
        return self.url_base

    def chgoffset(self, revision):
        return self._vtimes[revision]
        
    def xsvgbranches(self, c1, c2):
        """Provide the ordered list of branch widgets which are
        between two changeset wdigets"""
        a1 = c1.branch().vaxis()
        a2 = c2.branch().vaxis()
        branches = filter(lambda b,l=a1,r=a2: l<b.vaxis()<r, 
                          self._svgbranches.values())
        branches.sort() 
        return branches
        
    def fixup_point(self, point):
        """Avoid two operation path to go through the same point
           Store every points of an operation path. If the point is already
           marked as used, find another point, looking around the original
           point for a free slot"""
        (x, y) = point
        kx = int(x)
        if self._oppoints.has_key(kx):
            val = 1
            inc = 1
            while y in self._oppoints[kx]:
                y += val*(UNIT/3)
                val = -val + inc
                inc = -inc
        else:
            self._oppoints[kx] = []
        self._oppoints[kx].append(y)
        return (x, y)
        
    def svg(self):
        return self._svg

    def __str__(self):
        """Dump the revision tree as a SVG UTF-8 string"""
        import cStringIO
        xml=cStringIO.StringIO()
        self._svg.toXml(0, xml)
        return xml.getvalue()
        
    def save(self, filename):
        """Save the revision tree in a file"""
        d = SVG.drawing()
        d.setSVG(self._svg)
        d.toXml(filename)
        
    def render(self, scale=1.0):
        """Render the revision tree"""
        self._svg = SVG.svg((0, 0, self._extent[0], self._extent[1]),
                            scale*self._extent[0], scale*self._extent[1],
                            True, id='svgbox')
        self._arrows.render()
        map(lambda e: e.render(IRevtreeEnhancer.ZBACK), self._addons)
        map(lambda b: b.render(IRevtreeEnhancer.ZBACK), 
                               self._svgbranches.values())
        map(lambda e: e.render(IRevtreeEnhancer.ZMID), self._addons)
        map(lambda b: b.render(IRevtreeEnhancer.ZMID), 
                               self._svgbranches.values())
        map(lambda e: e.render(IRevtreeEnhancer.ZFORE), self._addons)
        map(lambda b: b.render(IRevtreeEnhancer.ZFORE), 
                               self._svgbranches.values())
        dbgDump(self._svg)

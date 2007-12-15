# Implements the Moin-style IncludePages macro.
#
# This plugin base on WikiInclude macro By Vegard Eriksen zyp at jvnv dot net.
# See: http://projects.edgewall.com/trac/wiki/MacroBazaar#WikiInclude
# and on the variant written by  yu-ji

from genshi.builder import Element, tag
from genshi.core import Markup

from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem, parse_args
from trac.wiki.model import WikiPage

import inspect
import re

import wikiaddress, geocode

__all__ = ['AddressMacro']

_API_KEY = 'ABQIAAAA3VM3oU5dUaRzj4mZKrWenRR-aua9fIhr0mssyA66j0SiUW84BRT6dpcTl-e73A90avaJpS5TGZYrCQ'

class AddressMacro(Component):
    """

    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Address'

    def get_macro_description(self, name):
        return inspect.getdoc(AddressMacro)

    def apiURL(self,api_key):
        ''' Create the API key for Google Maps
        '''
        return "<script type=\"text/javascript\" src=\"http://maps.google.com/maps?file=api&v=2&key=%s\"></script>\n"%(api_key)

    def basemap(self):
        ''' Render JavaScript that is common to every map
        '''
        out = '''\
        <script type="text/javascript">
        //<![CDATA[
        var baseIcon = new GIcon();
        baseIcon.shadow = "http://www.google.com/mapfiles/shadow50.png";
        baseIcon.iconSize = new GSize(20, 34);
        baseIcon.shadowSize = new GSize(37, 34);
        baseIcon.iconAnchor = new GPoint(9, 34);
        baseIcon.infoWindowAnchor = new GPoint(9, 2);
        baseIcon.infoShadowAnchor = new GPoint(18, 25);

        var pointIcon = new GIcon();
        pointIcon.shadow = "http://www.google.com/mapfiles/arrowshadow.png";
        pointIcon.iconSize = new GSize(39, 34);
        pointIcon.shadowSize = new GSize(37, 34);
        pointIcon.iconAnchor = new GPoint(9, 34);
        pointIcon.infoWindowAnchor = new GPoint(9, 2);
        pointIcon.infoShadowAnchor = new GPoint(18, 25);

        function createArrow(point,text) {
                var icon = new GIcon(pointIcon);
                icon.image = "http://www.google.com/mapfiles/arrow.png";
                var marker = new GMarker(point,icon);
                GEvent.addListener(marker,"click", function() {
                        marker.openInfoWindowHtml(text);
                });
                return marker;
        }
        function createMarker(point, index, text) {
                var letter = String.fromCharCode("A".charCodeAt(0) + index);
                var icon = new GIcon(baseIcon);
                icon.image = "http://www.google.com/mapfiles/marker" + letter + ".png";
                var marker = new GMarker(point, icon);

                GEvent.addListener(marker, "click", function() {
                        marker.openInfoWindowHtml(text);
                        });
                return marker;
        }
        function toggle(id) {
                var elem = document.getElementById(id);
                if(elem != null) {
                        if (elem.style.display == 'none') {
                                elem.style.display = '';
                        } else {
                                elem.style.display = 'none';
                        }
                }
        }
        //]]>
        </script>
        '''

        return out

    def singlemap(self,name,place,loctag,location,nearby):
        ''' Create a string containig javascript for google map
        place = place object of center of map
        loctag = location tag name for this point
        location = location name for this point
        nearby = dictionary of nearby places
        '''
        out = '''\
        <script type="text/javascript">
        //<![CDATA[
        var %s_mapon = false;
        var %s_loaded = false;

        function %s_load() {
            if (%s_loaded) return;
            '''%(loctag,loctag,loctag,loctag)
        out += '''\
            var map = new GMap2(document.getElementById("%sdiv"));
            map.addControl(new GSmallMapControl());
            map.addControl(new GMapTypeControl());
            '''%(loctag)
        out += '''\
                map.setCenter(new GLatLng(%s,%s),14);
                '''%(place.lat,place.long)
        out += '''\
                var cpoint = new GLatLng(%s,%s);
                '''%(place.lat,place.long)    

        if nearby is not None:
            i = 0
            for x in nearby:
                namestr = '''\'<b><a href="%s">%s</a></b><br>%s\''''\
                            %(x['name'].replace("'","\\"+"'"),
                            x['name'].replace("'","\\"+"'"),
                            x['address'].replace("'","\\"+"'"))
                out += '''
            var point = new GLatLng(%s,%s);
            map.addOverlay(createMarker(point,%s,%s));
            '''%(x['lat'],x['long'],i,namestr)
                i += 1
               
        else:
            out += '''// nearby is none lat=%s long=%s
            '''%(place.lat,place.long)

        if location is None or location == '':
            loctxt = name
        else:
            loctxt = name + '<br/>('+location+' Location)'
        out += '''map.addOverlay(createArrow(cpoint,"%s"));'''%(loctxt)
        out += '''
            %s_loaded = true;
        }
        //]]>
        </script>
        '''%(loctag)
                
        return out


    def expand_macro(self, formatter, name, txt):

        r1 = re.compile(r'^\s*\"(.+)\"\s*,\s*\"(.+)\"\s*$')
        if r1.search(txt):
            (address,location) = r1.search(txt).groups()
        else:
            address = txt.strip('"')
            location = None
        
        req = formatter.req
        author = req.authname
        ipnr = req.remote_addr
        resource = formatter.resource
        page = WikiPage(self.env,resource)
        name = page.name

        db = self.env.get_db_cnx()

        place = wikiaddress.wikiaddress(db,name,_API_KEY,author,
                                        ipnr,address,location)
        
        if place.lat is None:
            return address

        if location is None:
            loctag = 'l'
        else:
            loctag = 'l_'+location.replace(' ','')

        nearby = place.getNearby()

        # use the req object to store whether the base javascript has
        # been rendered.  don't do it twice
        out = ''
        if not hasattr(req,'addressmacro'):
            req.addressmacro = True
            out += self.apiURL(_API_KEY)
            out += self.basemap()

        out += self.singlemap(name,place,loctag,location,nearby)
        out += address+" <a onclick=\"javascript:toggle('"+loctag+"div');"+loctag+"_load();return false;\" href=\"\">"+" [View Map]"+"</a>"
        out += "<div id=\""+loctag+"div\" style=\"width: 450px; height: 300px;display: none;\"></div>"
      
        return out
        

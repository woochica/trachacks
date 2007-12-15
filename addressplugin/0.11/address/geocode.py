import sys, urllib, urllib2, urlparse, gzip, xml.dom.minidom
from StringIO import StringIO

class geocode:
    '''\
    geocode addresses using Google Maps 
    
    place = geocode.geocode(address,api_key)

    ele = place.ele
    lat = place.lat
    long = place.long
    
    Note that ele is always 0 for the current (2.0) version of
    the Maps API
    
    '''

    # be sure the URL is set correctly for google maps

    MAP_URL = 'http://maps.google.com/maps/geo?output=xml&'

    lat = None
    long = None
    ele = None
    debug = False

    def __init__(self,address,api_key,debug=False):
        if debug == True:
            self.debug = True
        self.api_key = api_key
        if address is not None:
            self.__getCoordinates(address)

    class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_301(self, req, fp, code, msg, headers):
            result = urllib2.HTTPRedirectHandler.http_error_301(
                self, req, fp, code, msg, headers)
            result.status = code
            return result

        def http_error_302(self, req, fp, code, msg, headers):
            result = urllib2.HTTPRedirectHandler.http_error_302(
                self, req, fp, code, msg, headers)
            result.status = code
            return result

    class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
        def http_error_default(self, req, fp, code, msg, headers):
            result = urllib2.HTTPError(
                req.get_full_url(), code, msg, headers, fp)
            result.status = code
            return result

    def __openURL(self,address):
        """URL --> string

        Open a URL and return the data as a string.  Use the smart
        handlers to deal with redirects and errors.  Accept gzip and
        handle it if we get it.

        Modified from the example in Dive Into Python
        """

        # open URL with urllib2
        address = urllib.urlencode({'q':address})
        myurl = self.MAP_URL + '&key=' + self.api_key + '&' + address 
        request = urllib2.Request(myurl)
        request.add_header('Accept-encoding', 'gzip')
        opener = urllib2.build_opener(self.SmartRedirectHandler(),\
                                      self.DefaultErrorHandler())
        f = opener.open(request)
        data = f.read()

        if hasattr(f, 'headers') and \
               f.headers.get('content-encoding') == 'gzip':
            # data came back gzip-compressed, decompress it
            data = gzip.GzipFile(fileobj=StringIO(data)).read()
            f.close()

        return data

    def __getCoordinates(self,address):
        """ address --> list of lat, long, altitude of the address

        At this time, altitude is always 0
        """

        # extremely rudimentary error handling

        try:
            xmlout = self.__openURL(address)
        except:
            return

        try:
            xmldoc = xml.dom.minidom.parseString(xmlout)
        except:
            return

        if self.debug: print xmlout

        # <Status><code> of 200 is good
        code = xmldoc.getElementsByTagName('code')
        if self.debug: sys.stderr.write("Code = '%s'" % code[0].childNodes[0].data)
        if code[0].childNodes[0].data != '200':
            return

        coord = xmldoc.getElementsByTagName('coordinates')
        try:
            self.long, self.lat, self.ele = \
                coord[0].childNodes[0].data.split(',')
        except:
            return

        if self.debug:
            sys.stderr.write("Lat = %s, Long = %s"%(self.lat,self.long))
           
        return

# end geocode

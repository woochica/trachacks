"""
module to deal with the iCal format:

http://tools.ietf.org/html/rfc2445
"""

import datetime
import re

from cStringIO import StringIO

CRLF = '\r\n'

class Property(object):
    def __init__(self, name, value, params=None):
        self.name = name
        self.value = value
        self.params = params or {}

class iCal(object):

    def __init__(self, writer=None, title=''):
        if writer is None:
            self.buffer = StringIO()
            writer = self.buffer.write
        self.title = title
        self.writer = writer

    ### methods stolen from Trac's roadmap module:
    ### http://trac.edgewall.org/browser/trunk/trac/ticket/roadmap.py

    def escape_value(self, text): 
        s = ''.join(map(lambda c: (c in ';,\\') and '\\' + c or c, text))
        return '\\n'.join(re.split(r'[\r\n]+', s))

    def write_prop(self, name, value, params={}):
        text = ';'.join([name] + [k + '=' + v for k, v in params.items()]) \
            + ':' + self.escape_value(value)
        firstline = 1
        while text:
            if not firstline: text = ' ' + text
            else: firstline = 0
            self.writer(text[:75] + CRLF)
            text = text[75:]

    ### methods for writing iCal

    def write_head(self, name):
        """
        * name: name of the calendar
        """
        __version__ = 0.11
        self.write_prop('BEGIN', 'VCALENDAR')
        self.write_prop('VERSION', '2.0')
        self.write_prop('PRODID', '-//Edgewall Software//NONSGML Trac %s//EN'
                   % __version__)
        self.write_prop('METHOD', 'PUBLISH')
        self.write_prop('X-WR-CALNAME', name)

    def write_events(self, events):

        for event in events:
            self.write_prop('BEGIN', 'VEVENT')
            for property in event:
                self.write_prop(property.name, property.value, property.params)
            self.write_prop('END', 'VEVENT')

    def write(self, name, events):
        self.write_head(name)
        self.write_events(events)
        self.write_prop('END', 'VCALENDAR')

        if hasattr(self, 'buffer'):
            # return the string and reset the buffer
            retval = self.buffer.getvalue()
            self.buffer = StringIO()
            return retval

    ### 

    try: 
        # feedparser should be installed for iCalExporterPlugin
        # however, this class can be used independently 
        # in this case feedparser may not be installed so only
        # have this method for the case when it is
        import feedparser

        def from_rss(self, url):
            """method for converting RSS -> iCal"""
            feed = self.feedparser.parse(url)
            events = []

            attrmap = { 
                        'link': 'URL',
                        'title': 'SUMMARY',
                        'summary': 'DESCRIPTION',
                        }

            for entry in feed.entries:
                event = []

                if entry.has_key('updated_parsed'):
                    args = list(entry.updated_parsed[:7])
                    #                tzinfo = datetime.tzinfo(entry.updated_parsed[-1]) # XXX i think?
#                args.append(tzinfo)
                    date = datetime.datetime(*args)
                    event.append(Property('DTSTAMP', date.strftime('%Y%m%dT%H%M%SZ')))
                    event.append(Property('DTSTART', date.strftime('%Y%m%d'),
                                          {'VALUE': 'DATE'}))
                event.append(Property('UID', '<%s;%s>' % (entry.link, entry.get('id', ''))))
                for key in attrmap:
                    if key in entry:
                        event.append(Property(attrmap[key], entry[key]))
                events.append(event)

            title = feed.feed.get('title', self.title)
            return self.write(title, events)

    except ImportError:
        pass

if __name__ == '__main__':
    ical = iCal()
    cal = ical.from_rss('http://trac.openplans.org/trac/ticket/10?format=rss')
    print cal

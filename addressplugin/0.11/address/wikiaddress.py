import geocode
import time
from trac.core import *

class wikiaddress:

    '''\
    wikiaddress.py -- db wrapper class to read/write/create wikiaddress rows
    
    place = wikiaddress.wikiaddress(self,env,name,location,address,lat,long,ele)

    lat = place.lat
    long = place.long

    uses the geocode class

    '''
#
    def __init__(self,db,name,api_key,author,ipnr,address,
                 location=None): 

        self.db = db
        self.api_key = api_key
        self.name = name
        self.author = author
        self.ipnr = ipnr

        if location is None:
            self.location = ''
        else:
            self.location = location
     
        # lookup the page name.  
        self.__lookupPlace()
        if self.address == address:
            return

        # missing or changed.  geocode the new addr
        # if it doesn't exist, add it
        # if it's changed, update it.
        self.__geocodePlace(address)
        if self.address is None:
            self.__addPlace(address)
        else:
            self.__updatePlace(address)

        return



    def __lookupPlace(self): 
        '''\
        private to lookup the name/location in the db
        sets address, lat, long, ele
        '''

        cursor = self.db.cursor()
        cursor.execute('''SELECT address, lat, `long`, ele
                          FROM wikiaddress
                          WHERE name = %(name)s 
                          and location = %(location)s ''',
                           {'name':self.name,
                            'location':self.location})
        row = cursor.fetchone()

        if row:
            self.address, self.lat, self.long, self.ele = row
        else:
            self.address = None
            self.ele = None
            self.lat = None
            self.long = None

        return

    def __geocodePlace(self,address):

        ''' get the lat/log/alt of the address '''

        place = geocode.geocode(address,self.api_key)
        self.lat = place.lat
        self.long = place.long
        self.ele = place.ele

    def __addPlace(self,address):

        ''' insert a location entry in the db '''

        cursor = self.db.cursor()
        cursor.execute('''INSERT INTO wikiaddress
                          VALUES (%(pagename)s,
                          %(location)s,
                          %(address)s,
                          %(lat)s,%(long)s,%(ele)s,
                          %(time)s,
                          %(author)s,
                          %(ipnr)s)''',
                       {'pagename':self.name,
                        'location':self.location,
                        'address' :address,
                        'lat':self.lat,
                        'long':self.long,
                        'ele':self.ele,
                        'time':time.time(),
                        'author':self.author,
                        'ipnr':self.ipnr})

    def __updatePlace(self,address):

        ''' update entry in db '''
     
     
        cursor = self.db.cursor()
        cursor.execute('''UPDATE wikiaddress
                       SET address = %(address)s,
                       lat = %(lat)s,
                       `long` = %(long)s
                       WHERE name = %(name)s and
                       location = %(location)s''',
                       {'address':address,
                        'lat':self.lat,
                        'long':self.long,
                        'name':self.name,
                        'location' :self.location })


    def getNearby(self,max=20,distance=.2):

        ''' create a list of nearby place, with a maximum
        number of places = max, and a radius of distance degrees '''

        cursor = self.db.cursor()
        cursor.execute('''SELECT name, location, address, lat, `long`
                        FROM wikiaddress
                        WHERE abs(abs(%(long1)s)-abs(`long`))+
                        abs(abs(%(lat1)s)-abs(lat)) < %(dist)s
                        AND name <> %(name)s
                        ORDER BY abs(abs(%(long2)s) - abs(`long`))+
                        abs(abs(%(lat2)s)-abs(lat)) 
                        LIMIT %(max)s''',
                       {'long1':self.long,
                        'lat1':self.lat,
                        'dist':distance,
                        'name':self.name,
                        'long2':self.long,
                        'lat2':self.lat,                      
                        'max':max})

        rows = cursor.fetchall()
        if rows: 
            lis = []
            for row in rows:
                lis.append({'name':row[0],'location':row[1],
                            'address':row[2],'lat':row[3],\
                            'long':row[4]})
            return lis
        else:
            return None

# end location

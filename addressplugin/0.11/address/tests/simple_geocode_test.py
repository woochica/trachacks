import sys
sys.path.append('../')
import geocode

_API_KEY = 'PUT YOUR KEY HERE'

place = geocode.geocode('1 Main St, Pittsford, NY 14534',_API_KEY)
print "Lat %s",place.lat
print "Long %s",place.long





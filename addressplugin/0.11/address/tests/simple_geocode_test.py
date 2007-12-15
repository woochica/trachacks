import sys
sys.path.append('../')
import geocode

_API_KEY = 'ABQIAAAA3VM3oU5dUaRzj4mZKrWenRR-aua9fIhr0mssyA66j0SiUW84BRT6dpcTl-e73A90avaJpS5TGZYrCQ'

place = geocode.geocode('1 Main St, Pittsford, NY 14534',_API_KEY)
print "Lat %s",place.lat
print "Long %s",place.long





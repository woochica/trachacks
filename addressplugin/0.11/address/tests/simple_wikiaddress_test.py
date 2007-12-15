import sys
sys.path.append('../')
import wikiaddress

_API_KEY = 'ABQIAAAA3VM3oU5dUaRzj4mZKrWenRR-aua9fIhr0mssyA66j0SiUW84BRT6dpcTl-e73A90avaJpS5TGZYrCQ'

my_dbapi = __import__("MySQLdb")
mydb = my_dbapi.connect(host='localhost',
                        user='rottentrac',
                        passwd='rottentrac',
                        db='rottentrac')

w = wikiaddress.wikiaddress(mydb,'mundo grill',_API_KEY,'somebody','1.2.3.4','2833 Monroe Ave, Rochester NY 14618',None)

nb = w.getNearby()

print "Lat=%s,Long=%s"%(w.lat,w.long)
if nb is None:
    print "NB is empty"
else:
    for x in nb:
        print "name = %s, address=%s, lat=%s, long=%s"%(x['name'],x['address'],x['lat'],x['long'])

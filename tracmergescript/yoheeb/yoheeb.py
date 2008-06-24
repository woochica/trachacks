import sys
sys.path.append('..')
from ptrac import Trac
import csv
import time

t = Trac('../test/testenv1')

CSV = 'ticketsToAdd.csv'

tickets = csv.DictReader(open(CSV))

for tick in tickets:
	tick['id'] = int(tick['id'])
	tick['time'] = int(time.time())
	tick['changetime'] = int(time.time())
	tick['ticket_change'] = []
	tick['attachment'] = []
	t.addTicket(tick, '')

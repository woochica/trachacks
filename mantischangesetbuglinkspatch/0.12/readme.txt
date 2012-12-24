1. Apply icachechangesetlistener.env.diff patch

wget http://python-patch.googlecode.com/svn-history/trunk/patch.py
python patch.py icachechangesetlistener.env.diff
rm patch.py

2. Change MANTIS_URL value in plugins/mantis_tickets_query.py to point to
   location of your bug tracker
3. Copy changed plugins/mantis_tickets_query.py to your Trac environment

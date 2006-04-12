from trac.util import escape
from StringIO import StringIO
import csv

def execute(hdf, txt, env):
    sniffer = csv.Sniffer()
    reader = csv.reader(StringIO(txt), dialect=sniffer.sniff(txt))
    out = StringIO()
    out.write('<table class="wiki">\n')
    for row in reader:
        out.write('<tr>')
        for col in row:
            out.write('<td>%s</td>' % escape(col))
        out.write('</tr>\n')
    out.write('</table>\n')
    return out.getvalue()

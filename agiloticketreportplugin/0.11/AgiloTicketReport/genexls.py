#!/usr/bin/env python
#coding=utf-8

from pyExcelerator import *

class ExcelGenerator:
    def writeExcelReport(self,list, name):
        w = Workbook()
        ws = w.add_sheet(name)
        ws.write(1,1, "ticket id")
        ws.write(1,2, "summary")
        ws.write(1,3, "owner")
        ws.write(1,4, "estimated time(hours)")
        ws.write(1,5, "cost time(hours)")
    
        for row in range(2, list.__len__()+2):
            obj = list.pop(0)
            ws.write(row, 1, obj.id)
            ws.write(row, 2, obj.summary)
            ws.write(row, 3, obj.owner)
            ws.write(row, 4, int(obj.esti_hours.__str__()))
            ws.write(row, 5, obj.cost_hours)
        w.save('TicketReport' + name +'xls')
        
import pgdb
pgdb_conn = pgdb.connect(host='localhost',database='trac_db',user='postgres',password='nicehp')
cur = pgdb_conn.cursor()
cur.execute("SELECT * FROM swfcq.attachment WHERE filename ='"+file_name+"'")

if cur.fetchone() is None:
    print cur.fetchone()
    cur.execute("INSERT INTO swfcq.attachment(\"type\", id, filename) VALUES('report', 'ticket_report','"+file_name+"')")
    pgdb_conn.commit()
    pgdb_conn.close()
                 

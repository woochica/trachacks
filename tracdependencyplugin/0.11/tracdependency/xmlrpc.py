import xmlrpclib
import posixpath

from trac.core import *
from trac.perm import IPermissionRequestor
from tracrpc.api import IXMLRPCHandler, expose_rpc
from trac.util.text import to_unicode
import time
import datetime

class WorkHoursRPC(Component):
    """ Interface to the [http://trac-hacks.org/wiki/TracDependencyPlugin TracDependency Plugin] """
    implements(IXMLRPCHandler)

    def __init__(self):
        pass

    def xmlrpc_namespace(self):
        return 'dependency'

    def xmlrpc_methods(self):
        yield ('TICKET_VIEW', ((list, str, str),), self.executeQuery)
        yield ('TICKET_VIEW', ((list, str),), self.getWorkHourChangeTimes)
        yield ('TICKET_VIEW', ((list, str),), self.getWorkHourChanges)
        yield ('TICKET_VIEW', ((list, int),), self.getWorkHours)
        yield ('TICKET_VIEW', ((list, int),), self.getWorkHoursPriod)

    def executeQuery(self, req, query, sort):
        """Returns results of query"""
        #クエリーを実行します．
        if query == "":
            query = "t.id>0"
        if sort == "":
            sort = "t.id"
        sql = "SELECT "
        sql = sql + "t.id, "
        sql = sql + "t.type, "
        sql = sql + "t.component, "
        sql = sql + "t.severity, "
        sql = sql + "t.priority, "
        sql = sql + "t.owner, "
        sql = sql + "t.reporter, "
        sql = sql + "t.cc, "
        sql = sql + "t.version, "
        sql = sql + "t.milestone, "
        sql = sql + "t.status, "
        sql = sql + "t.resolution, "
        sql = sql + "t.summary, "
        sql = sql + "t.description, "
        sql = sql + "due_assign.value as 'due_assign', "
        sql = sql + "due_close.value as 'due_close', "
        sql = sql + "complete.value as 'complete', "
        sql = sql + "summary_ticket.value as 'summary_ticket', "
        sql = sql + "dependencies.value as 'dependencies', "
        sql = sql + "hours.value as 'hours', "
        sql = sql + "estimatedhours.value as 'estimatedhours', "
        sql = sql + "billable.value as 'billable', "
        sql = sql + "baseline_start.value as 'baseline_start', "
        sql = sql + "baseline_finish.value as 'baseline_finish', "
        sql = sql + "baseline_cost.value as 'baseline_cost', "
        sql = sql + "blocking.value as 'blocking' "
        sql = sql + "FROM ticket t "
        sql = sql + "LEFT JOIN ticket_custom due_assign ON due_assign.ticket = t.id AND due_assign.name='due_assign' "
        sql = sql + "LEFT JOIN ticket_custom due_close ON due_close.ticket = t.id AND due_close.name='due_close' "
        sql = sql + "LEFT JOIN ticket_custom complete ON complete.ticket = t.id AND complete.name='complete' "
        sql = sql + "LEFT JOIN ticket_custom summary_ticket ON summary_ticket.ticket = t.id AND (summary_ticket.name='summary_ticket' OR summary_ticket.name='parent') "
        sql = sql + "LEFT JOIN ticket_custom dependencies ON dependencies.ticket = t.id AND dependencies.name='dependencies' "
        sql = sql + "LEFT JOIN ticket_custom hours ON hours.ticket = t.id AND hours.name='hours' "
        sql = sql + "LEFT JOIN ticket_custom estimatedhours ON estimatedhours.ticket = t.id AND estimatedhours.name='estimatedhours' "
        sql = sql + "LEFT JOIN ticket_custom billable ON billable.ticket = t.id AND billable.name='billable' "
        sql = sql + "LEFT JOIN ticket_custom baseline_start ON baseline_start.ticket = t.id AND (baseline_start.name='baseline_start' OR baseline_start.name='plan_start') "
        sql = sql + "LEFT JOIN ticket_custom baseline_finish ON baseline_finish.ticket = t.id AND (baseline_finish.name='baseline_finish' OR baseline_start.name='plan_end') "
        sql = sql + "LEFT JOIN ticket_custom baseline_cost ON baseline_cost.ticket = t.id AND baseline_cost.name='baseline_cost' "
        sql = sql + "LEFT JOIN ticket_custom blocking ON blocking.ticket = t.id AND blocking.name='blocking' "
        sql = sql + "WHERE " + query
        sql = sql + " GROUP BY " + sort
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql)
        result = []
        for row in cursor:
            d={}
            d['id']=row[0]
            d['type']=row[1]
            d['component']=row[2]
            d['severity']=row[3]
            d['priority']=row[4]
            d['owner']=row[5]
            d['report']=row[6]
            d['cc']=row[7]
            d['version']=row[8]
            d['milestone']=row[9]
            d['status']=row[10]
            d['resolution']=row[11]
            d['summary']=row[12]
            d['description']=row[13]
            d['due_assign']=row[14]
            d['due_close']=row[15]
            d['complete']=row[16]
            d['summary_ticket']=row[17]
            d['dependencies']=row[18]
            d['hours']=row[19]
            d['estimatedhours']=row[20]
            d['billable']=row[21]
            d['baseline_start']=row[22]
            d['baseline_finish']=row[23]
            d['baseline_cost']=row[24]
            d['blocking']=row[25]
            for k in d.keys():
                if d[k] == None:
                    d[k] = ""
            result.append(d)
        return result

    def getWorkHourChangeTimes(self, req, id):
        """Returns a list of changetimes"""
        #時間関連のフィールドが変更された時間の一覧を返します．
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if id == 0:
	        sql="SELECT DISTINCT time FROM ticket_change WHERE (field='totalhours' OR  field='estimatedhours' OR  field='baseline_cost') GROUP BY time"
        else:
	        sql="SELECT DISTINCT time FROM ticket_change WHERE (field='totalhours' OR  field='estimatedhours' OR  field='baseline_cost') AND ticket='%s' GROUP BY time" % id
        cursor.execute(sql)
        result = []
        for row in cursor:
            #result.append(row[0])
            result.append(xmlrpclib.DateTime(datetime.datetime.fromtimestamp(row[0])))
        return result

    def getWorkHourChanges(self, req, id):
        """Returns a list of changetime records"""
        #ticket_changeの時間関連のすべてのレコードを返します．
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if id == 0:
	        sql="SELECT * FROM ticket_change WHERE (field='totalhours' OR  field='estimatedhours' OR  field='baseline_cost') GROUP BY time"
        else:
	        sql="SELECT * FROM ticket_change WHERE (field='totalhours' OR  field='estimatedhours' OR  field='baseline_cost') AND ticket='%s' GROUP BY time" % id
        cursor.execute(sql)
        result = []
        for row in cursor:
            d={}
            d['ticket']=row[0]
            d['time_iso']=xmlrpclib.DateTime(datetime.datetime.fromtimestamp(row[1]))
            d['time']=row[1]
            d['author']=row[2]
            d['field']=row[3]
            d['newvalue']=row[5]
            result.append(d)
        return result

    def getWorkHoursPriod(self, req, id):
        """Returns a list of changetime records"""
        #時間関連の値が変更のあった最初と最後の時間を返します．
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if id == 0:
	        sql="SELECT MIN(time), MAX(time), COUNT(ticket) FROM ticket_change WHERE (field='totalhours' OR  field='estimatedhours' OR  field='baseline_cost') "
        else:
	        sql="SELECT MIN(time), MAX(time), COUNT(ticket) FROM ticket_change WHERE (field='totalhours' OR  field='estimatedhours' OR  field='baseline_cost') AND ticket='%s'" % id
        cursor.execute(sql)
        result = []
        for row in cursor:
            result.append(row[0])
            result.append(row[1])
            #result.append(xmlrpclib.DateTime(datetime.datetime.fromtimestamp(row[0])))
            #result.append(xmlrpclib.DateTime(datetime.datetime.fromtimestamp(row[1])))
        return result

    def getWorkHours(self, req, id):
        """Returns a table of changetime records"""
        # 
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql="SELECT DISTINCT t.time, t1.newvalue, t2.newvalue, t3.newvalue FROM ticket_change t"
        sql = sql + " LEFT JOIN ticket_change t1 ON t1.time = t.time AND t1.field='totalhours'"
        sql = sql + " LEFT JOIN ticket_change t2 ON t2.time = t.time AND t2.field='estimatedhours'"
        sql = sql + " LEFT JOIN ticket_change t3 ON t3.time = t.time AND t3.field='baseline_cost'"
        sql = sql + " WHERE t.ticket='%s'" % id
        sql = sql + " AND (t.field='totalhours' OR  t.field='estimatedhours' OR  t.field='baseline_cost')"
        #sql = sql + " GROUP BY t.time"
        cursor.execute(sql)
        result = []
        totalhours=""
        estimatedhours=""
        baseline_cost=""
        for row in cursor:
            d={}
            d['time']=row[0]
            d['time_iso']=xmlrpclib.DateTime(datetime.datetime.fromtimestamp(row[0]))
            if row[1] == None:
                d['totalhours']=totalhours
            else:
                d['totalhours']=row[1]
                totalhours=row[1]
            if row[2] == None:
                d['estimatedhours']=estimatedhours
            else:
                d['estimatedhours']=row[2]
                estimatedhours=row[2]
            if row[3] == None:
                d['baseline_cost']=baseline_cost
            else:
                d['baseline_cost']=row[3]
                baseline_cost=row[3]
            if totalhours != "":
                result.append(d)
        return result




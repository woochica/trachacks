# -*- coding: utf-8 -*-
import os,sys,time,datetime,pickle
import adodb

from ini import Settings, sqltrac

import logging
#----------------------------------------------------------------------------
abspath = os.path.abspath(sys.argv[0])
dirname = os.path.dirname(abspath)

daylog = "%s"%(time.strftime("%y%m%d",time.localtime()))
logging.basicConfig(level=logging.DEBUG,
                   format='[%(asctime)s]%(levelname)-8s"%(message)s"',
                    datefmt='%Y-%m-%d %a %H:%M:%S',
                    filename=os.path.join(dirname, 'log/burn-%s.log'%daylog),
                    filemode='a+')


''''burndown.py'
    - v0.8~080128 support 4 peg:#213
    - v0.7~080123 fixed for peg:#110
    - v0.6~080122 creat for peg:#110
'''
VERSION = "burndown.py v0.8 by Zoom.Quiet"


class burndown:
    """main class zip all done:
        - for KISS rule every time rebuild all
    """
    def __init__(self,milestone):
        """ini all:
            - milestone milestone
        """
        self.milestone=milestone
        self.init = Settings
        self.mapDone=('closed')
        self.mapDoing=('assigned')
        self.mapNew=('new', 'reopened')
        self.mapUnplan=('accidental')

        # load setting from ini
        self.fDict = os.path.join(dirname, "%s/%s.dump"%(self.init['dumpath'],milestone))
        self.expRoot = self.init['expath']
        self.projname = self.init['projname']
        self.rootpath = self.init['rootpath']
        self.dbname = self.init['dbname']

        self.sqls = sqltrac
        self.conn = adodb.NewADOConnection('sqlite') # pysqlite required

        dbf = "%s/%s/%s"%(self.rootpath
            ,self.projname
            ,self.dbname)
        self.conn.Connect(database = dbf) #"trac.db"

        try:
            print "try load historic dictDUMP"
            self.TicketQuery = pickle.load(open(self.fDict))

        except: 
            print "rebuild dict.obj."
            self.TicketQuery={}
        '''data struc.
        burnti={
                'yymmdd':{'burn':{'due':int,'all':[id,...]}
                    ,'total':{'due':int,'all':[id,...]}
                    }
                ,...        
        }
        '''

        day = 60*60*24

        
#        reAllTi = self.conn.GetAll(self.sqls['allTickets'])
        timeMin = self.conn.GetOne(self.sqls['timeMin'] % self.milestone)
        if not timeMin:
            return

        dayMin = int(timeMin) / day
        today = int(time.time()) / day

        for aDay in range(dayMin, today + 1):
            d = time.strftime("%y%m%d",time.localtime(aDay * day))
            print d
            rows = self.conn.GetAll(self.sqls['allTicketsOneDay'] % self.milestone)

            reAllTi = []
            for row in rows:
                id = row[0]
                t = (aDay + 1) * day
                currentStatus = self.conn.GetAll(self.sqls['currentStatus'] % (id, t))[0][0]
                if not currentStatus:
                    result = self.conn.GetAll(self.sqls['createdStatus'] % (id, t))
                    if result:
                        currentStatus = result[0][0]

                if currentStatus:
                    row = list(row)
                    row[-4] = currentStatus
                    reAllTi.append(row)
#            print reAllTi

            reAllDue = self.conn.GetAll(self.sqls['allDue'] % self.milestone)
#            reAllDue = self.conn.GetAll(self.sqls['allDue'])


            # filter history record, i.e., not today or yesterday
            if aDay != today and aDay != today -1 and self.TicketQuery.has_key(d):
                    print "skipped %s" % d
                    continue
            else:
                self.TicketQuery[d] = self.initScan(reAllTi, reAllDue)#DBscanner()
#                print self.TicketQuery

            print "%s >>>CreatDate flush starting.."%(self.projname)
            logging.info("%s >>>CreatDate flush starting.."%self.projname)

            f = open(self.fDict,"w")
            pickle.dump(self.TicketQuery,f)
            f.close()

    def initScan(self, reAllTi, reAllDue):
        """scan data for query all:    
        """

        crtDue = {'burn':{'due':0,'all':[]}
            ,'doing':{'due':0,'all':[]}
            ,'new':{'due':0,'all':[]}
            ,'unplan':{'due':0,'all':[]}#accidental
            ,'total':{'due':0,'all':[]}
            }
        doneTi = []

        for i in reAllTi:
            id = i[0]
            status = i[-4]
            milestone = i[-1]

            if milestone.startswith(self.milestone):
                crtDue['total']['all'].append(id)
                if self.mapDone == status:
                    doneTi.append(id)
                elif self.mapDoing == status:
                    crtDue['doing']['all'].append(id)
                elif status in self.mapNew:
                    crtDue['new']['all'].append(id)
                if self.mapUnplan in i[1]:
                    crtDue['unplan']['all'].append(id)

        for d in reAllDue:
            id = d[0]
            value = d[-1]

            if id in doneTi:
                crtDue['burn']['all'].append(id)
                crtDue['burn']['due'] += self.dueday(value)
            if id in crtDue['total']['all']:
                crtDue['total']['due'] += self.dueday(value)


        print "%s >>>crt Tickets::%s "%(
            self.projname,len(reAllTi))
        logging.info("%s >>>current Tickets::%s "%(
            self.projname,len(reAllTi)))

        print "%s >>>scanned full DB done!"%(self.projname)
        logging.info("%s >>>scanned full DB done!"%(self.projname))

        return crtDue


    def dueday(self,due):
        """merge due time as WorkDay    
        """
        #print due,due[-1:]
        if 'd'==due[-1:]:
            return float(due[:-1])
        elif 'w'==due[-1:]:
            return float(due[:-1])*5
        elif 'm'==due[-1:]:
            return float(due[:-1])*20
        else:
            #usage h
            return float(0.5)



    def expChart(self):
        '''call pychartdir doing... 
        '''
        from extchart import extstate

        chart = extstate(self.milestone,os.path.join(dirname, self.init['expath']),self.TicketQuery)
        chart.hisChart(self.init['defont'])

        return


if __name__ == '__main__':
    '''default running
    '''
    if 3 != len(sys.argv):
        print """ %s usage::
        $ python burndown.py milestone
        """ % VERSION
    else:
        begin = time.time()
        milestone = sys.argv[1]
        q4burn = burndown(milestone)
        q4burn.expChart()

        end = time.time()
        print "q4burn flush end.."
        logging.info("q4burn flush end..")
        print "usedTime::%s(s)%s"%((end - begin),"~"*27)
        logging.info("usedTime::%s(s) %s"%((end - begin),"~"*27) )


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
                    filename=os.path.join(dirname, 'log/relati-%s.log'%daylog),
                    filemode='a+')


''''relaticket.py'
    - v0.8~080221 fixed for peg:#262
    - v0.7~080128fixed for exp. HTML TAB
    - v0.6~080127 creat for peg:#213
'''
VERSION = "relaticket.py v0.8~080221 by Zoom.Quiet"



class relaticket:
    """main class zip all done:
        - for KISS rule every time rebuild all
    """
    def __init__(self,milestone):
        """ini all:
            - milestone ~milestone
        """
        self.crtDate = time.strftime("%y%m%d",time.localtime(time.time()))
        self.milestone=milestone
        self.init = Settings
        self.done=('closed')    
        self.TicketQuery = {}    
        self.RelaTicket = {'relati':{}
            ,'purenew':[]
            ,'puredoing':[]
            ,'puredone':[]
            }
        
        # load setting from ini
        self.fDict = os.path.join(dirname, "data/%s.dump"%milestone)
        self.expRoot = self.init['expath']
        self.projname = self.init['projname']
        self.rootpath = self.init['rootpath']
        self.dbname = self.init['dbname']
        self.reporturl = self.init['reporturl']
        #self.UnplannedRep = self.init['UnplannedRep']
        self.ticketurl = self.init['ticketurl']


        self.tplIdx = os.path.join(dirname, "%s/idx.relat.tpl"%self.init['tplpath'])
        self.expIdx = os.path.join(dirname, "%s/idx-%s.html"%(self.init['expath'],milestone))
        
        
        self.sqls = sqltrac
        #print self.sql
        self.conn = adodb.NewADOConnection('sqlite') # pysqlite required
        
        dbf = "%s/%s/%s"%(self.rootpath
            ,self.projname
            ,self.dbname)
        print dbf
        self.conn.Connect(database = dbf) #"trac.db"
        
        
        try:
            print "try load historic dictDUMP"
            self.MaileQuery = pickle.load(open(self.fDict))[self.crtDate]
        except: 
            print "BurnDown data can't load! %s" % self.crtDate
            print pickle.load(open(self.fDict))
            logging.info("%s >>>BurnDown data can't load!.."%self.projname)
            return
            #self.MaileQuery={}
        
        #print self.MaileQuery 
        '''data struc.
        burnti={
                'yymmdd':{'burn':{'due':int,'all':[id,...]}
                    ,'total':{'due':int,'all':[id,...]}
                    }
                ,...        
        }
        SELECT p.value AS __color__, t.priority as __group__,id AS ticket, summary, 
        time AS created FROM ticket t LEFT JOIN enum p ON p.name = t.priority AND p.type = 'priority' 
        WHERE milestone = 'DefendEngine.m1.\u9632\u5fa1\u5b50\u7cfb\u7edf\u7b2c\u4e00\u9636\u6bb5\u70b9' and status = 'assigned' ORDER BY p.value
        
        '''
        
        
        
        
        self.crtAllTi = self.initScan()#DBscanner()
        #print self.crtAllTi
        print "%s >>>CreatDate flush starting.."%(self.projname)
        logging.info("%s >>>CreatDate flush starting.."%self.projname)
        
        
        #print "selected items:: ",len(self.result)
    
    
    def putItem(self,tmpDict,ti):
        '''try the only matter:
            - try push into tmpDict need info.
        '''
        reDict = self.TicketQuery
        reDict[ti[0]]={
            'type':ti[1]
            ,'time':ti[2]
            ,'changetime':ti[3]
            ,'component':ti[4]
            ,'severity':ti[5]
            ,'priority':ti[6]
            ,'owner':ti[7]
            ,'reporter':ti[8]
            ,'status':ti[9]
            ,'resolution':ti[10]
            ,'summary':ti[-2]
            ,'milestone':ti[-1]}
    
        #print "pushed %s KO"%ti[0]
    
    
    def initScan(self):
        """scan data for query all:    
        """
        reDict = self.TicketQuery
        relatAll = self.RelaTicket
        reAllTi = self.conn.GetAll(self.sqls['allTickets'])
        tmpDict = self.TicketQuery
        for i in reAllTi:
            self.putItem(tmpDict,i)
        #print tmpDict[190]
        
        '''collection done tickets
            - if had 'alldone' key, means main tickets is done
        '''
        #print self.MaileQuery
        try:
            for id in self.MaileQuery['burn']['all']:
                summary = tmpDict[id]['summary']
                if '<#'== summary[:2]:
                    parentID = summary.split(">")[0][2:]
                    if parentID in relatAll['relati'].keys():
                        relatAll['relati'][parentID]['done'].append(id)
                    else:
                        relatAll['relati'][parentID] = {'doing':[],'done':[]}
                        relatAll['relati'][parentID]['done'].append(id)
                else:
                    parentID = summary.split(">")[0][2:]
                    if parentID in relatAll['relati'].keys():
                        relatAll['relati'][parentID]['alldone']=''
                    else:
                        relatAll['puredone'].append(id)
        except:
            pass
        
        
                 
        '''collection doing tickets
            - if had 'alldoing' key, means main tickets is doing
        '''
        try:
            for id in self.MaileQuery['doing']['all']:
                summary = tmpDict[id]['summary']
                if '<#'== summary[:2]:
                    parentID = summary.split(">")[0][2:]
                    if parentID in relatAll['relati'].keys():
                        relatAll['relati'][parentID]['doing'].append(id)
                    else:
                        relatAll['relati'][parentID] = {'doing':[],'done':[]}
                        relatAll['relati'][parentID]['doing'].append(id)
                else:
                    parentID = summary.split(">")[0][2:]
                    if parentID in relatAll['relati'].keys():
                        relatAll['relati'][parentID]['alldoing']=''
                    else:
                        relatAll['puredoing'].append(id)
        except:
            pass
        
        
        
        '''collection new tickets
            - 'subnew' key collection, assigned tickets 
        '''
        #print self.MaileQuery['new']['all']
        #print relatAll
        try:
            for id in self.MaileQuery['new']['all']:
                #print id
                summary = tmpDict[id]['summary']
                if '<#'== summary[:2]:
                    #print summary
                    parentID = summary.split(">")[0][2:]
                    #print parentID
                    
                    if parentID in relatAll['relati'].keys():
                        print "Item in new::%s<#%s>"%(id,parentID)
                        
                        if 'subnew' in relatAll['relati'][parentID].keys():
                            relatAll['relati'][parentID]['subnew'].append(id)
                        else:
                            relatAll['relati'][parentID]['subnew']=[]
                            relatAll['relati'][parentID]['subnew'].append(id)
                        
                        
                    else:
                        print "jump here?do %s"%id
                        relatAll['relati'][parentID] = {'doing':[],'done':[]}
                        
                        if 'subnew' in relatAll['relati'][parentID].keys():
                            relatAll['relati'][parentID]['subnew'].append(id)
                        else:
                            relatAll['relati'][parentID]['subnew']=[]
                            relatAll['relati'][parentID]['subnew'].append(id)
                        
                        
                else:
                    #print summary
                    if id in relatAll['relati'].keys():
                        pass
                    else:
                        relatAll['purenew'].append(id)
                    
                    '''
                    parentID = summary.split(">")[0][2:]
                    if parentID in relatAll['relati'].keys():
                        print  parentID
                        if 'subnew' in relatAll['relati'][parentID].keys():
                            relatAll['relati'][parentID]['subnew'].append(parentID)
                        else:
                            relatAll['relati'][parentID]['subnew']=[]
                            relatAll['relati'][parentID]['subnew'].append(parentID)
                    else:
                        relatAll['purenew'].append(id)
                    '''
        except:
            pass
        print relatAll
        #print relatAll['relati'].keys()
        
        
        
        
        #print relatAll['relati']
        
        
        
       
        print "%s >>>crt Tickets::%s "%(
            self.projname,len(reAllTi))
        logging.info("%s >>>current Tickets::%s "%(
            self.projname,len(reAllTi)))
        #for item in reTickets[120]: print item
    
        #pickle.dump(reDict,open(self.fDict,"w"))
        
        print "%s >>>scanned full DB done!"%(self.projname)
        logging.info("%s >>>scanned full DB done!"%(self.projname))
        return tmpDict
    
    
    
    
    def expHTML(self):
        '''usage simple TPL support exp. HTML page
        '''
        myVer = VERSION
        reporturl = self.reporturl
        #UnplannedRep = self.UnplannedRep
        projname = self.projname
        optproj = self.milestone
        creaTime = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        reDict = self.RelaTicket
        #print self.MaileQuery.keys()
        maileDict = self.MaileQuery
        relatickets = ""
        #print self.TicketQuery.keys()
        #print reDict['relati']['155']['subnew']
        for rti in reDict['relati'].keys():
            ti = int(rti)
            relatickets +="<tr>"
            #main tickets
            relatickets +="<td><ul>"
            relatickets +='''<li>
                <a href="%s/%s">%s::%s</a>
                '''%(self.ticketurl,ti
                    ,ti
                    ,self.TicketQuery[ti]['summary'].encode('utf8')
                    )
            if 'subnew' in reDict['relati'][rti].keys():
                #had not doing sub news ti
                relatickets +="<ul>"
                for ti in reDict['relati'][rti]['subnew']:
                    relatickets +='''<li>
                        `~ <i><a href="%s/%s">%s::%s</a></i>
                        </li>
                        '''%(self.ticketurl,ti
                            ,ti
                            ,self.TicketQuery[ti]['summary'].encode('utf8')
                            )
                relatickets +="</ul></li>"
            else:
                relatickets += "</li>"
            
            
            
            relatickets +="</ul></td>"
            #main 's doing tickets
            
            relatickets +="<td><ul>"
            for id in reDict['relati'][rti]['doing']:
                relatickets +='''<li>
                    <a href="%s/%s">%s::%s</a>
                    </li>
                    '''%(self.ticketurl,id
                        ,id
                        ,self.TicketQuery[id]['summary'].encode('utf8')
                        )
            relatickets +="</ul></td>"
            
            
            
            #main 's done tickets
            
            relatickets +="<td><ul>"
            for id in reDict['relati'][rti]['done']:
                relatickets +='''<li>
                    <a class='closed' href="%s/%s">
                    %s::%s</a>
                    </li>
                    '''%(self.ticketurl,id
                        ,id
                        ,self.TicketQuery[id]['summary'].encode('utf8')
                        )
            relatickets +="</ul></td>"
            
            
            
            
            relatickets +="</tr>"
        
        
        purenew = ""
        for ti in reDict['purenew']:
            purenew += '''<li>
                <a href='%s/%s'>#%s::%s</a>
                </li>'''%(self.ticketurl,ti
                    ,ti
                    ,self.TicketQuery[ti]['summary'].encode('utf8')
                    )
        
        
        
        
        puredoing = ""
        for ti in reDict['puredoing']:
            puredoing += '''<li>
                <a href='%s/%s'>#%s::%s</a>
                </li>'''%(self.ticketurl,ti
                    ,ti
                    ,self.TicketQuery[ti]['summary'].encode('utf8')
                    )
        
        puredone = ""
        for ti in reDict['puredone']:
            puredone += '''<li>
                <a class='closed' href='%s/%s'>#%s::%s</a>
                </li>'''%(self.ticketurl,ti
                    ,ti
                    ,self.TicketQuery[ti]['summary'].encode('utf8')
                    )
        
        unplan = ""
        
        for ti in maileDict['unplan']['all']:
            unplan += '''<li>
                <a href='%s/%s'>#%s::%s</a>
                </li>'''%(self.ticketurl,ti
                    ,ti
                    ,self.TicketQuery[ti]['summary'].encode('utf8')
                    )
        
        open(self.expIdx,"w").write(open(self.tplIdx).read() % locals())
        print "%s >>>exp.ed relation @ %s..."%(self.projname
            ,self.crtDate)
        logging.info("%s >>>exp.ed relation @ %s..."%(self.projname
            ,self.crtDate))
        return
    


if __name__ == '__main__':
    '''default running
    '''
    if 3 != len(sys.argv):
        print """ %s usage::
        $ python relaticket.py milestone yymmdd
        """ % VERSION
    else:
        begin = time.time()
        milestone = sys.argv[1]
        q4relat = relaticket(milestone)
        q4relat.expHTML()
        
        end = time.time()
        print "q4relat flush end.."
        logging.info("q4relat flush end..")
        print "usedTime::%s(s)%s"%((end - begin),"~"*27)
        logging.info("usedTime::%s(s) %s"%((end - begin),"~"*27) )


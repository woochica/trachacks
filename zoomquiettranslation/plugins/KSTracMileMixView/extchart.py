# -*- coding: utf-8 -*-
import os,sys,time,datetime,pickle
from ChartDirector.pychartdir import *
'''install under Python
/usr/local/lib/python2.5/site-packages> sudo mkdir ChartDirector

'''

''''extchart.py'
    - v1.4 080407 fixed for long milestone
    - v1.3 080128 fixed img width
    - v1.2 080123 done BurnDown line export
    - v1.1 080122 merage for KXE
    - v1.0 070903 fixed for some crash for loast "PV"?!
    - v0.9 070802 append month flush judge
    - v0.8 070726 appent PIE chart support
    - v0.7 070725 creat 
'''
VERSION = "extchart v1.4 by Zoom.Quiet"

class extstate:
    """main class zip all done
    """
    def __init__(self,projName,expath,data):
        """ini all
        """
        #print data
        self.projName = projName
        self.data = data
        self.hisPNG = "%s/%s-burndown.png"%(expath,projName)
        #print self.hisPNG
        self.dlist = data.keys()
        #print self.dlist
        self.dlist.sort()
        self.dlist.reverse()#.sort()
        #print self.dlist
        self.dueli = []
        for d in self.dlist:
            deltaDue = data[d]['total']['due']-data[d]['burn']['due']
            self.dueli.append(deltaDue)

        # remove leading zero
        dueliNew = []
        dlistNew = []
        i = 0
        for d in self.dueli:
            if d != 0:
                dueliNew = self.dueli[i:]
                dlistNew = self.dlist[i:]
                break
            i += 1
            
        self.dueli = dueliNew
        self.dlist = dlistNew

    
    def hisChart(self, defaultfont):
        '''利用ChartDirector Ver 4.1 (Python Edition)绘制图表
            - 历史趋势图
        '''
        print "ChartDirector Ver 4.1 drawing ..."
        
        # The data for the line chart
        hisDue = self.dueli
        labels = self.dlist



        cdrTitle = "BurnDown 4 %s "%self.projName
        
        pwidth = len(labels)*18
        cwidth = 80+pwidth
        #pheight = 2*int(self.data[labels[-1]]['total']['due'])#len(labels)*15
        hs = [int(self.data[label]['total']['due']) for label in labels]
        if hs:
            pheight = 2 * max(hs)
        else:
            pheight = 10

        cheight = 100+pheight
        
        #c = XYChart(cwidth,250, 0xffffc0, 0x000000, 1)
        c = XYChart(cwidth,cheight, 0xffffc0, 0x000000, 1)
        #c.swapXY()
        #c.setYAxisOnRight()
        
        c.addLegend(40, 15, 0, "", 8).setBackground(Transparent)
        #c.setPlotArea(60,60, 140,pheight, 0xffffff, 0xeeeeee)
        #c.setPlotArea(60, 60, 140,pheight, 0xffffff, -1, -1, 0xc0c0c0, -1)
        c.setPlotArea(40, 50, pwidth,pheight
            , c.linearGradientColor(0, 35, 0, 235, 0xf9fcff,0xaaccff)
            , -1, Transparent, 0xffffff)
        
        c.setBackground(goldColor(), 0x334433, 1) #metalColor(0xccccff)
        c.setRoundedFrame()
        c.setDefaultFonts(defaultfont)
        
        c.addTitle(cdrTitle,defaultfont, 11,0xffffff
            ).setBackground(c.patternColor([0x004000, 0x008000], 2))
    
        c.yAxis().setLabelFormat("{value}")
        c.xAxis().setLabels(labels).setFontAngle(30)#.setFontAngle(90)
        #c.xAxis().setReverse()
        c.xAxis().setWidth(2)
        c.yAxis().setWidth(2)
        
        layer = c.addSplineLayer() #addLineLayer()
        layer.setLineWidth(4)
        layer.addDataSet(hisDue, 0xcf4040, "Due(day)").setDataSymbol(CircleSymbol, 9,0xffff00)
        layer.setDataLabelFormat("{value|1}")
        layer.setDataLabelStyle(defaultfont,8,0x334433,-90)
    
        c.makeChart(self.hisPNG)
        ## 输出可点击区域定义
        '''
        imageMap = c.getHTMLImageMap("replayed/yueku-play-{xLabel}.html"
            , "date={xLabel}"
            , "title='{xLabel}:: {value|0} '")
        return imageMap
        '''

if __name__ == '__main__':      # this way the module can be
    if 3 != len(sys.argv):
        print """ %s usage::
        $ python extstate.py 'path/to/stxihei.ttf' datePoint [like 070501]
        """ % VERSION
    else:
        begin = time.time()
        defaultfont = sys.argv[1]           #[-10:-4]    print tonow
        #log/file [like log/070704play.log]
        tonow = sys.argv[2]                 #[-10:-4]    print tonow
        ps = extstate(tonow,defaultfont,"YKext STATs")
        ps.main()
        
        end = time.time()
        print ">>>usedTime::%.2fs<<<"%(end - begin)
        
    print "Mnnnn export all that report!!!!"


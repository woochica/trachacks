#!/usr/bin/env python
#coding=utf-8
'''

Calculate working time

@author: Tod
'''
import datetime
import time

WORKING_START_TIME = 9
WORKING_END_TIME = 18
ONE_NIGHT_SECOND = 3600*15
HOLIDAYS = [datetime.datetime(2009,10,1), datetime.datetime(2009,10,2)]

class GetWorkingHours:

    def isWorkingDay(self, _date):
        for oneday in HOLIDAYS:
            if _date.year == oneday.year and _date.month == oneday.month and _date.day == oneday.day:
                return False
        return (_date.weekday() != 5 and _date.weekday() != 6)
    
    def getExtraWorkingHours(self, _date_, _is__start_date):
        if self.isWorkingDay(_date_):   
            if _date_.hour < WORKING_START_TIME :
                if _is__start_date:
                    return WORKING_END_TIME - WORKING_START_TIME
                else:
                    return 0
            elif _date_.hour < WORKING_END_TIME:
                if _is__start_date:
                    return WORKING_END_TIME - _date_.hour - round(float(_date_.minute)/60, 2)
                else:
                    return _date_.hour - WORKING_START_TIME + round(float(_date_.minute)/60, 2)                    
            else:
                if not _is__start_date:
                    return WORKING_END_TIME - WORKING_START_TIME
                else:
                    return 0
        else:
            return 0
    
    
    def getTotalWorkingHours(self, accepted_obj, closed_obj):
        accepted_time = time.localtime(accepted_obj)
        closed_time = time.localtime(closed_obj)
        _start_date = datetime.datetime(accepted_time[0],accepted_time[1],accepted_time[2],accepted_time[3],accepted_time[4],accepted_time[5])
        _end_date = datetime.datetime(closed_time[0],closed_time[1],closed_time[2],closed_time[3],closed_time[4],closed_time[5])        
        if _start_date > _end_date:
            #  handler ..
            print "start_date:"+_start_date.__str__()+" end_date:"+_end_date.__str__()+" data mistake(start_date should before end_date)"
            return 0
        elif _start_date.year == _end_date.year \
            and _start_date.month == _end_date.month \
                and _start_date.day == _end_date.day:
            working_hours = round(float(time.mktime(_end_date.timetuple()) - time.mktime(_start_date.timetuple()))/3600, 2)
        else:
            working_hours = self.getExtraWorkingHours(_start_date, True) + self.getExtraWorkingHours(_end_date, False)
            workingonedays = -1
            while ((time.mktime(_end_date.timetuple()) - time.mktime(_start_date.timetuple())) > ONE_NIGHT_SECOND):
                if self.isWorkingDay(_start_date):                
                    workingonedays += 1
                _start_date += datetime.timedelta(days = 1)         
            if workingonedays <= 0:
                workingonedays = 1
            else:
                working_hours += workingonedays*(WORKING_END_TIME - WORKING_START_TIME)
            
        return working_hours

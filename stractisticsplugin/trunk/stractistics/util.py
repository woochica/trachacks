# -*- coding: utf-8 -*-
#
# Stractistics
# Copyright (C) 2008 GMV SGI Team <http://www.gmv-sgi.es>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# $Id: util.py 432 2008-07-11 12:58:49Z ddgb $
#

import OpenFlashChart

def read_config_options(config):
    """
    Reads available configurations options from trac.ini 
    """
    options = {}
    repository_authors_limit = config.getint('stractistics',\
                                                'repository_authors_limit', 5)
    options['repository_authors_limit'] = repository_authors_limit
        
    repository_ignored_authors = [str(elem) for elem in config.getlist(\
                                                'stractistics',
                                                'ignored_repository_authors',
                                                default=[])]
    options['repository_ignored_authors'] = repository_ignored_authors
        
    wiki_authors_limit = config.getint('stractistics', 
                                                    'wiki_authors_limit', 5)
    options['wiki_authors_limit'] = wiki_authors_limit
        
    wiki_ignored_authors = [str(elem) for elem in config.getlist(\
                                                'stractistics',
                                                'ignored_wiki_authors',
                                                default=[])]
    options['wiki_ignored_authors'] = wiki_ignored_authors
        
    max_author_characters = config.getint('stractistics', 
                                                    'max_author_characters', 
                                                    None)
    options['max_author_characters'] = max_author_characters
    return options 


def datetime_to_secs(datetime_date):
    """ 
    From datetime to seconds since epoch. 
    """
    import calendar 
    return calendar.timegm(datetime_date.timetuple())

def parse_time_gap(req, data):
    """
    Parse 'end_date' and 'weeks_back' from url.
    In case of error, end_date defaults to current date
     and weeks_back defaults to 12.
    """
    
    weeks_back = 12
    if req.args.has_key('weeks_back'):
        try:
            tmp = int(req.args['weeks_back'])
            if tmp > 0:
                weeks_back = tmp
        except ValueError:
            pass
    data['weeks_back'] = weeks_back
    
    import datetime
    end_date = datetime.datetime.today()
    date_format = "%m/%d/%y"
    if req.args.has_key('end_date'):
        aux = req.args['end_date']
        try:
            aux = datetime.datetime.strptime(aux, date_format)
            end_date = aux
        except Exception:
            end_date = datetime.datetime.today()
    data['end_date'] = datetime.datetime.strftime(end_date, 
                                                               date_format)
    start_date = end_date - datetime.timedelta(days = weeks_back * 7)
    return start_date, end_date, weeks_back


def swap_week_year(x):
    """
    From "Year-Week" to "Week-Year".It just swaps places.
    "Year-Week" format is much easier to sort but for displaying purposes
    "Week/Year" is preferable.
    """
    aux = x.split('/')
    return "%s/%s" % (aux[1], aux[0])
    
def remove_duplicates(list):
    #Not very efficient.
    dic = {}
    for elem in list:
        dic[elem] = None
    return dic.keys()

def execute_sql_expression(db, sql_expr, map_rows = lambda x:x):
    """
    By default, this function returns a list of rows, each row is a tuple.
    """
    cursor = db.cursor()
    cursor.execute(sql_expr)
    results = [map_rows(elem) for elem in cursor]
    db.commit()
    return results

def sort_values_by_key(dic):
    """
    Returns a list of the values in dic sorted by key.
    """
    keys = dic.keys()
    keys.sort()
    return map(dic.get, keys)

def format_to_week(datetime):
    """
    Picks a datetime and formats it into a "Year/Week" string.
    """
    format = "%y/%W"
    return datetime.strftime(format)

def get_weeks_elapsed(start_date, end_date):
    """
    Returns a dic whose keys are all the weeks between start_date and 
    end_date.
    """
    import datetime
    #Sometimes the 53th week of the year is just one day long. If we skip 
    #that week but data has been generated in 
    #that week, the plugin will crash because of a KeyError.
    diff = datetime.timedelta(days=1)
    weeks = {}
    myDate = start_date
    while myDate < end_date:
        weeks[format_to_week(myDate)] = 0
        myDate = myDate + diff
    weeks[format_to_week(end_date)] = 0
    return weeks    

def adapt_to_table(weeks_list, authors_data, config):
    """
    This function rearranges our data in order to be displayed easier 
    in the html table.
    """
        
    #First, we reverse the order of the weeks.
    reversed_weeks_list = list(weeks_list)
    reversed_weeks_list.reverse()
        
    """Now, we must reverse the order of the results to match the new 
    order of weeks.""" 
    results = {}
    for author in authors_data.iterkeys():
        results[author] = list(authors_data[author])
        results[author].reverse()
        
    """
    Every row in rows is a 2-tuple, the first element of the tuple is the 
    week and the second element of the tuple is an array of the wiki 
    modifications per author for that week.
    """
    authors = results.keys()
    rows = []
    index = 0
    for week in reversed_weeks_list:
        week_N_values = []
        for author in authors:
            week_N_values.append(results[author][index])
        index += 1
        rows.append((week, week_N_values))
        
    #Name mangling goes here
    def mangle_name(name, characters_cap):
        if characters_cap is not None and characters_cap > 0:
            name = name[0:characters_cap]
        return name
    
    columns = [mangle_name(name, config['max_author_characters']) \
                    for name in authors]
    return (columns, rows)

def restructure_data(authors_data):
    """
    We need this function to avoid employing names with dots as HDF nodes.
    """
    new_data = []
    for author in authors_data.keys():
        dic = {}
        dic['author'] = author
        dic['info'] = authors_data[author]
        new_data.append(dic)
    return new_data        


class QueryResponse:
    """
    Encapsulates the information retrieved by a query and additional data for 
    correct display.
    """
    def __init__(self,name, path='/chrome'):
        self.title = None
        self.name = name
        self.columns = []
        self.results = []
        self.path = "".join([path, '/hw/swf/'])
        self.chart_info = ChartInfo(name, self.path)
        
    def set_name(self,name):
        self.name = name
        self.chart_info.name = "%s_chart" % self.name
    
    def set_title(self, title):
        self.title = title
        self.chart_info.title = title
        
    def set_columns(self, columns):
        self.columns = columns
        
    def set_results(self, results):
        self.results = results
        size = len( results )
        self.chart_info.data_size = size
    
    def get_data(self):
        return {
                'title':self.title,
                'columns':self.columns,
                'results':self.results,
                'chart_info': self.chart_info.get_data()
                }
    
        
class ChartInfo:
    """
    This data is meant to be fed to SWF objects.
    It lets us control chart presentation.
    """
    def __init__(self,name='',path=''):
        #Default values
        self.width = 480
        self.height = 300
        self.x_font_size = 10
        self.x_font_color = "#000000"
        self.y_max = 0
        self.y_steps = 8
        self.data_size = 0
        self.x_orientation = 2
        self.x_steps = 1
        self.bg_color = '#FFFFFF'
        self.x_axis_color = '#000000'
        self.y_axis_color = '#000000'
        self.x_grid_color = '#F2F2EA'
        self.y_grid_color = '#F2F2EA'
        self.tool_tip = '#key#<br>#x_label#<br>#val#'
        self.type = "Bar"
        self.x_labels = None
        self.data = None
        self.colors = ["#f79910","#cbcc99","#6498c1","#cb1009","#64b832",
                       "#FF69B4","#000000","#8470FF"]
        self.title = ''
        self.name = "%s_chart" % name
        self.path = path
    
    def embed(self):
        chartObject = OpenFlashChart.graph_object()
        return chartObject.render(self.width, self.height,'',
                                  self.path, ofc_id = self.name) 

    #Only useful if you wish a custom tool_tip. 
    def set_tool_tip(self, tool_tip):
        self.tool_tip = tool_tip
    
    #Only useful for pie charts
    def set_line_color(self, color):
        self.line_color = color
               
    def set_width(self, width):
        self.width = width 
        
    def set_height(self, height):
        self.height = height
        
    def get_data(self):
        members_dic = {}
        for member in dir(self):
            if not callable(getattr(self,member)) and member[0] != "_":
                members_dic[member] = getattr(self, member)
        return members_dic

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
# $Id: global_reports.py 432 2008-07-11 12:58:49Z ddgb $
#

from util import *

def global_reports(req, config, db):
    data = {}
    start_date, end_date, weeks_back = parse_time_gap(req, data)
    #First , repository activity 
    data['repository_activity'] = _repository_activity(req, config,
                                          start_date, end_date, 
                                          weeks_back, db)
        
    #Second, ticket activity.
    data['ticket_activity'] = _ticket_activity(req, config, end_date, db)
                
    #Third, wiki activity.
    data['wiki_activity'] = _wiki_activity(req, config, 
                                            start_date, end_date, 
                                            weeks_back, db)
    return 'global_reports.html', data

def _repository_activity(req, config, start_date, end_date, weeks_back, db):
    """
    Displays commits per week of the AUTHORS_LIMIT most active authors in 
    the last WEEKS_NUMBER weeks.
    """
    WEEKS_NUMBER = weeks_back
    AUTHORS_LIMIT = config['repository_authors_limit']
    ignored_authors = _quote_authors(config['repository_ignored_authors'])        
    

    #We retrieve the most active authors during the time frame
    authors = _most_active_repository_authors( AUTHORS_LIMIT, 
                                               ignored_authors, 
                                               start_date,
                                               end_date,
                                               db)
    #Now we retrieve all the revisions commited in the time frame
    revisions = _retrieve_revisions(authors, start_date, end_date, db)        
    #Last, for every author we determine how many commits per week he's done. 
    weeks_list, authors_data = _authors_commit_data(authors, revisions, 
                                                    start_date, end_date,db)        
    #We must build a QueryResponse from weeks_labels, and authors_data
    query_response = QueryResponse("repository_activity", req.href('/chrome'))
    query_response.set_title("Commits per week (%s weeks)" % WEEKS_NUMBER)
    
    columns, rows = adapt_to_table(weeks_list, authors_data, config)
    query_response.set_columns(columns)
    query_response.set_results(rows)   
    
    chart = query_response.chart_info
    chart.type = 'Line'
    chart.x_legend = 'Weeks'
    chart.y_legend = 'Commits'
    chart.x_labels = weeks_list
    chart.data = restructure_data(authors_data) 
    chart.set_tool_tip("#key#<br>week:#x_label#<br>commits:#val#")
         
    return query_response
        
def _most_active_repository_authors(AUTHORS_LIMIT, ignored_authors, start_date, 
                                    end_date, db):
    """
    Retrieves the AUTHORS_LIMIT most active repository authors between 
    start_date and end_date.
    Returns a list with their names.
    """
    authors = []
    sql_expr = """
    SELECT r.author AS author, COUNT( r.author ) AS commits 
     FROM revision r 
     WHERE r.time > %s AND r.time < %s %s
     GROUP BY r.author 
     ORDER BY commits DESC 
     LIMIT %s
    """
    def ignoreList(authors):
        if not authors:
            return ""
        return "AND r.author NOT IN ( %s )" % ','.join( map(lambda x:"'%s'" % x, authors) )
    sql_expr = sql_expr % ( datetime_to_secs(start_date),
                                      datetime_to_secs(end_date),
                                      ignoreList(ignored_authors),
                                      AUTHORS_LIMIT)
    
    def map_rows(row):
        return row[0]
    authors = execute_sql_expression(db, sql_expr, map_rows)
    return authors 
    
    
def _retrieve_revisions(authors, start_date, end_date, db):
    """
    Retrieves every revision commited by any author in authors between start_date and end_date
    Returs a list of author and date pairs.
    """
    revisions = []
    sql_expr = """
    SELECT r.author AS author, r.time AS date
    FROM revision r 
    WHERE r.time > %s AND r.time < %s %s
    """   

    def valuesList(authors):
        if not authors:
            return ""
        return "AND r.author IN ( %s )" % ','.join( map(lambda x:"'%s'" % x, authors) )
    
    sql_expr = sql_expr % (datetime_to_secs(start_date),
                                     datetime_to_secs(end_date),
                                     valuesList(authors))
    def map_rows(row):
        import datetime
        return (row[0],datetime.datetime.fromtimestamp(row[1]))
    revisions = execute_sql_expression(db, sql_expr, map_rows)
    return revisions

        
def _authors_commit_data(authors, revisions, start_date, end_date, db):
    """
    First, we obtain the list of weeks between start_date and end_date.
    Then for each author we compute how many commits he's done each week.
    """
    weeks = get_weeks_elapsed(start_date,end_date)
    authors_data = {}
    for aut in authors:
        authors_data[aut] = weeks.copy()
    for rev in revisions:
        author = rev[0]
        week = format_to_week(rev[1])
        authors_data[author][week] = authors_data[author][week] + 1
    
    weeks_labels = [k for k in weeks.iterkeys()]
    weeks_labels.sort()
    weeks_labels = [swap_week_year(x) for x in weeks_labels]
    
    aux_dic = {}
    for author in authors_data.iterkeys():
        aux_dic[author] = sort_values_by_key(authors_data[author])
    authors_data = aux_dic
    return (weeks_labels, authors_data)
     

def _ticket_activity(req, config, end_date, db):
    """
    Shows ticket activity in the last NUM_DAYS days, only those tickets 
    created or modified during that time frame are considered. 
    """
    NUM_DAYS = 30
    
    sql_expr = """
    SELECT t.status AS status, COUNT(DISTINCT t.id) AS tickets
    FROM ticket t 
    WHERE t.changetime > %s
    GROUP BY t.status;
    """
    
    import datetime, calendar
    start_date = end_date - datetime.timedelta(days = NUM_DAYS)
    start_date = calendar.timegm(start_date.timetuple())
    
    sql_expr = sql_expr % start_date

    def map_rows(row):
        return (row[0],row[1])
    results = execute_sql_expression(db, sql_expr, map_rows)

    query_response = QueryResponse("ticket_activity", req.href('/chrome'))
    query_response.set_title("Ticket activity (%s days until %s)" % 
                             (NUM_DAYS, end_date.date()))
    query_response.set_columns(('ticket status','tickets'))
    query_response.set_results(results)
    chart = query_response.chart_info
    chart.type = "Pie"
    chart.set_width(480)
    chart.set_height(300)
    chart.set_tool_tip("status:#x_label#<br>tickets:#val#")
    chart.set_line_color("#000000")
    chart.x_labels = [row[0] for row in results]
    chart.data = [row[1] for row in results]
    
    return query_response
    
def _wiki_activity(req, config, start_date, end_date, weeks_back, db):
    """
    Displays wiki editions per week of each of the AUTHORS_LIMIT most 
    active authors in the last WEEKS_NUMBER weeks.
    """
    WEEKS_NUMBER = weeks_back
    AUTHORS_LIMIT = config['wiki_authors_limit']
    ignored_authors = _quote_authors(config['wiki_ignored_authors'])
            
    authors_list = _retrieve_most_active_wiki_authors(AUTHORS_LIMIT,
                                                      ignored_authors,
                                                      start_date,
                                                      end_date,
                                                      db)        
    wiki_pages_list = _retrieve_wiki_pages(start_date, end_date, db)        
    
    weeks_list, authors_data = _wiki_authors_data(authors_list, 
                                                  wiki_pages_list, 
                                                  start_date, 
                                                  end_date)
    
    
    query_response = QueryResponse("wiki_activity", req.href('/chrome'))
    query_response.set_title("Wiki activity (%s weeks)" % WEEKS_NUMBER)
    
    columns, rows = adapt_to_table(weeks_list, authors_data, config)
    query_response.set_columns(columns)
    query_response.set_results(rows)
    
    chart = query_response.chart_info
    chart.type = 'Line'
    chart.x_labels = weeks_list
    chart.x_legend = 'Weeks'
    chart.y_legend = 'Wiki modifications'
    chart.data = restructure_data(authors_data)
    chart.set_tool_tip("#key#<br>week:#x_label#<br>wiki modifications:#val#")
    
    return query_response
    
    
def _wiki_authors_data(authors_list, wiki_pages_list,
                            start_date, end_date):
    """
    We iterate over wiki_pages_list and for each wiki page edition, we
    increment the counter of the correspondent author and week.
    """
    weeks_dic = {}
    weeks_dic = get_weeks_elapsed(start_date, end_date)
    
    authors_data = {}
    for author in authors_list:
        authors_data[author] = weeks_dic.copy()
    
    for page in wiki_pages_list:
        week = format_to_week(page[1])
        author = page[0]
        if author in authors_list:
            authors_data[author][week] = authors_data[author][week] + 1
    
    #Sorting time!
    weeks_list = [key for key in weeks_dic.iterkeys()]
    weeks_list.sort()
    weeks_list = [swap_week_year(week) for week in weeks_list]
    
    data_aux = {}
    for author in authors_data:
        data_aux[author] = sort_values_by_key(authors_data[author])
    authors_data = data_aux
    return (weeks_list, authors_data)
                
        
def _retrieve_most_active_wiki_authors(AUTHORS_LIMIT, ignored_authors,
                                            start_date, end_date, db):
    """
    Retrieves the AUTHORS_LIMIT most active wiki authors between start_date
     and end_date
    """
    sql_expr = """
    SELECT w.author AS author, COUNT(distinct w.version) AS modifications 
    FROM wiki w
    WHERE w.time > %s AND w.time < %s %s
    GROUP BY author
    ORDER BY modifications DESC
    LIMIT %s  
    """
    import datetime
    def ignoreList(authors):
        if not authors:
            return ""
        return "AND w.author NOT IN ( %s )" % ','.join( map(lambda x:"'%s'" % x, authors) )
    sql_expr = sql_expr % (datetime_to_secs(start_date),
                                     datetime_to_secs(end_date),
                                     ignoreList(ignored_authors),
                                     AUTHORS_LIMIT)
    
    authors_list = execute_sql_expression(db, sql_expr, lambda row:row[0])
    return authors_list
    
def _retrieve_wiki_pages(start_date, end_date, db):
    sql_expr = """
    SELECT w.author AS author, w.time  AS time
    FROM wiki w
    WHERE time > %s AND time < %s
    """
    sql_expr = sql_expr % (datetime_to_secs(start_date),
                                     datetime_to_secs(end_date))
    
    def map_rows(row):
        import datetime
        return (row[0], datetime.datetime.fromtimestamp(row[1]))
    
    wiki_pages_list = execute_sql_expression(db, sql_expr, map_rows)
    return wiki_pages_list        
            
def _quote_authors(ignored_authors):
    """
    Returns a list of quoted authors in order to be able to use it with the 
    SQL IN operator.
    """
    def quote(author):
        return "'%s'" % author
    return ", ".join([quote(author) for author in ignored_authors])

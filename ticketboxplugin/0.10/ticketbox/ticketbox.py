# This plugin base on TicketBox macro
# Author: Jacques Witté

from __future__ import generators

try:
    from StringIO import StringIO
except ImportError:
    from StringIO import StringIO

from trac.core import *
from trac.wiki.formatter import wiki_to_html
from trac.wiki.api import IWikiMacroProvider, WikiSystem

import inspect

__all__ = ['TicketBoxMacro']

import re
import string
from trac import __version__ as version
from trac.wiki.formatter import wiki_to_oneliner
from trac.ticket.report import ReportModule
    
class TicketBoxMacro(Component):
    """
    Display list of ticket numbers in a box on the right side of the page.
    The purpose of this macro is show related tickets compactly.
    You can specify ticket number or report number which would be expanded
    as ticket numbers. Tickets will be displayed as sorted and uniq'ed.
    
    Example:
    {{{
    [[TicketBox(#1,#7,#31)]]               ... list of tickets
    [[TicketBox(1,7,31)]]                  ... '#' char can be omitted
    [[TicketBox({1})]]                     ... expand report result as ticket list
    [[TicketBox([report:1])]]              ... alternate format of report
    [[TicketBox([report:9?name=val])]]     ... report with dynamic variable
    [[TicketBox({1),#50,{2},100)]]         ... convination of above
    [[TicketBox(500pt,{1})]]               ... with box width as 50 point
    [[TicketBox(200px,{1})]]               ... with box width as 200 pixel
    [[TicketBox(25%,{1})]]                 ... with box width as 25%
    [[TicketBox('Different Title',#1,#2)]] ... Specify title
    [[TicketBox(\"Other Title\",#1,#2)]]     ... likewise
    [[TicketBox('%d tickets',#1,#2)]]      ... embed ticket count in title
    }}}
    
    [wiki:TracReports#AdvancedReports:DynamicVariables Dynamic Variables] 
    is supported for report. Variables can be specified like
    {{{[report:9?PRIORITY=high&COMPONENT=ui]}}}. Of course, the special
    variable '{{{$USER}}}' is available. The login name (or 'anonymous)
    is used as $USER if not specified explicitly.
    """
    implements(IWikiMacroProvider)
    ## NOTE: CSS2 defines 'max-width' but it seems that only few browser
    ##       support it. So I use 'width'. Any idea?


    def get_macros(self):
        yield 'TicketBox'

    def get_macro_description(self, name):
        return inspect.getdoc(TicketBoxMacro)
    
    def sqlstr(x):
        """Make quoted value string for SQL."""
        return "'%s'" % x.replace( "'","''" )
        
        
        
    def render_macro(self, req, name, txt):
        env = self.env 
        hdf = req.hdf
        
        
        
        # get trac version
        ver = [int(x) for x in version.split(".")]
        
        ## default style values
        styles = { "float": "right",
                   "background": "#f7f7f0",
                   "width": "25%",
                   }
        inline_styles = { "background": "#f7f7f0", }
        
        args_pat = [r"#?(?P<tktnum>\d+)",
                    r"{(?P<rptnum>\d+)}",
                    r"\[report:(?P<rptnum2>\d+)(?P<dv>\?.*)?\]",
                    r"(?P<width>\d+(pt|px|%))",
                    r"(?P<jourshomme>jourshomme)",
                    r"(?P<table_report>table_report)",
                    r"(?P<ticket_report>ticket_report)",
                    r"(?P<do_not_group_none>do_not_group_none)",
                    r"(?P<summary>summary)",
                    r"(?P<inline>inline)",
                    r"(?P<title1>'.*')",
                    r'(?P<title2>".*")']
                
                
    ##def execute(hdf, txt, env):
        if not txt:
            txt = ''
        items = []
        long_items = {}
        show_summary = False
        inline = False
        title = "Tickets"
        table_report_option = False
        ticket_report_option = False
        do_not_group_none = True
        theader =''
        args_re = re.compile("^(?:" + string.join(args_pat, "|") + ")$")
        for arg in [string.strip(s) for s in txt.split(',')]:
            match = args_re.match(arg)
            if not match:
                env.log.debug('TicketBox: unknown arg: %s' % arg)
                continue
            elif match.group('title1'):
                title = match.group('title1')[1:-1]
            elif match.group('title2'):
                title = match.group('title2')[1:-1]
            elif match.group('width'):
                styles['width'] = match.group('width')
            elif match.group('tktnum'):
                items.append(int(match.group('tktnum')))
            elif match.group('summary'):
                show_summary = True
            elif match.group('table_report'):
                table_report_option = True
            elif match.group('ticket_report'):
                ticket_report_option = True
            elif match.group('do_not_group_none'):
                do_not_group_none = False                
            elif match.group('inline'):
                inline = True
        for arg in [string.strip(s) for s in txt.split(',')]:
            match = args_re.match(arg)          
            if match.group('rptnum') or match.group('rptnum2'):
                num = match.group('rptnum') or match.group('rptnum2')
                dv = {}
                # username, do not override if specified
                if not dv.has_key('USER'):
                    dv['USER'] = hdf.getValue('trac.authname', 'anonymous')
                if match.group('dv'):
                    for expr in string.split(match.group('dv')[1:], '&'):
                        k, v = string.split(expr, '=')
                        dv[k] = v
                #env.log.debug('dynamic variables = %s' % dv)
                db = env.get_db_cnx()
                curs = db.cursor()
                try:
                    curs.execute('SELECT query FROM report WHERE id=%s' % num)
                    (query,) = curs.fetchone()
                    # replace dynamic variables with sql_sub_vars()
                    # NOTE: sql_sub_vars() takes different arguments in
                    #       several trac versions.
                    #       For 0.10 or before, arguments are (req, query, args)
                    #       For 0.10.x, arguments are (req, query, args, db)
                    #       For 0.11 or later, arguments are (query, args, db)
                    if ver <= [0, 10]:
                        args = (req, query, dv)     # for 0.10 or before
                    elif ver < [0, 11]:
                        args = (req, query, dv, db) # for 0.10.x
                    else:
                        args = (query, dv, db)      # for 0.11 or later
                    query, dv = ReportModule(env).sql_sub_vars(*args)
                    #env.log.debug('query = %s' % query)
                    curs.execute(query, dv)
                    rows = curs.fetchall()
                    if rows:
                        descriptions = [desc[0] for desc in curs.description]
                        
                        env.log.debug('TEST %s' % descriptions)
                        
                        for descriptions_item in descriptions:
                            theader = theader + '<td> %s </td>' % descriptions_item
                        
                        if do_not_group_none == False:
                          idx = descriptions.index('milestone')                        
                        else:
                          idx = descriptions.index('ticket')
                          
                        for row in rows:    
                            items.append(row[idx])                        
                            
                            if table_report_option:
                                table_field = ''
                                for descriptions_item in descriptions:
                                  if descriptions_item == 'ticket':
                                    table_field = table_field + '<td> %s </td>' % wiki_to_oneliner("#%s" % row[descriptions.index(descriptions_item)],env, env.get_db_cnx())
                                  else:
                                    table_field = table_field + '<td> %s </td>' % row[descriptions.index(descriptions_item)]
                                long_items[row[idx]] =  table_field                                
                            elif ticket_report_option:
                                table_field = ''
                                for descriptions_item in descriptions:
                                  if descriptions_item == 'ticket':
                                    table_field = table_field +'<li>'+descriptions_item+': %s' % wiki_to_oneliner("#%s" % row[descriptions.index(descriptions_item)],env, env.get_db_cnx())+'</li>'
                                  elif descriptions_item !='description' and descriptions_item !='summary':                                
                                    table_field = table_field +'<li>'+descriptions_item+': %s, ' % row[descriptions.index(descriptions_item)]+'</li>'
                                  long_items[row[idx]] =  '<b>%s</b><br/>'% row[descriptions.index('summary')] +'<ul>'+table_field+' </ul>'+ wiki_to_html(row[descriptions.index("description")] or '', env, req, env.get_db_cnx())
                            else:
                                summ = descriptions.index('summary')
                                long_items[row[idx]] = row[summ]
                finally:
                    if not hasattr(env, 'get_cnx_pool'):
                        # without db connection pool, we should close db.
                        curs.close()
                        db.close()
                        
        y=[]
        for i in items:
            if not y.count(i):
                y.append(i)
        
        items = y
        items.sort()
        html = ''
        tfooter =''
        if show_summary:
            html = string.join([wiki_to_oneliner("%s (#%d)" % (v,k),
                                                 env, env.get_db_cnx()) for k,v in long_items.iteritems()], "<br>")    
        elif table_report_option:
            for k,v in long_items.iteritems():
                if "#%s" %k == "#None" and do_not_group_none and do_not_group_none:
                  tfooter =  "<tfoot>%s</tfoot>" % v
                else:
                  html = html + "<tr>%s</tr>" % v
        elif ticket_report_option:
            for k,v in long_items.iteritems():
                if "#%s" %k != "#None":
                  html = html + "%s" % v
        else:
            html = wiki_to_oneliner(string.join(["#%s" % c for c in items], ", "),
                                    env, env.get_db_cnx())
                                    
        if html != '':
            try:
                title = title % len(items)  # process %d in title
            except:
                pass
            if inline:
                style = string.join(["%s:%s" % (k,v) for k,v in inline_styles.items() if v <> ""], "; ")
            else:
                style = string.join(["%s:%s" % (k,v) for k,v in styles.items() if v <> ""], "; ")
            
            if table_report_option:
                return '<table border=1><caption>'+title+'</caption><thead>'+theader+'</thead><tbody>'+html+'</tbody>'+tfooter+'</table>'
            if ticket_report_option:
                return html
            else:
                return '<fieldset class="ticketbox" style="%s"><legend>%s</legend>%s</fieldset>' % \
                   (style, title, html)
        else:
            return ''                                
    
         

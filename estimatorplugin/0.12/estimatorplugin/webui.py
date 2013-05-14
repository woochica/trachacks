import re

from genshi.template import TemplateLoader
from pkg_resources import resource_filename
from trac.core import *
from trac.ticket import Ticket
from trac.util import Markup
from trac.util.datefmt import to_utimestamp, to_datetime, to_timestamp
from trac.versioncontrol.diff import get_diff_options, diff_blocks
from trac.web import IRequestHandler
from trac.web.api import IRequestFilter
from trac.web.chrome import add_stylesheet, add_script, INavigationContributor, ITemplateProvider, Chrome

from estimatorplugin import dbhelper
from estimatorplugin.estimator import *

import trac.ticket.model
from trac.resource import ResourceNotFound

def ensure_component (env, name, owner=None):
    try:
        return trac.ticket.model.Component(env, name)
    except ResourceNotFound:
        c = trac.ticket.model.Component(env)
        c.name = name
        c.owner = owner
        c.insert()
        return c

def avg(low, high):
    low = convertfloat(low)
    high = convertfloat(high)
    if not low or low==0: return high;
    elif not high or high==0: return low;
    else: return (high + low)/2

def convertfloat(x):
    "some european countries use , as the decimal separator, never return not a float (0 will be returned if its a bad value)"
    if not x or type(x) == float: return x
    x = str(x).strip()
    try:
        if len(x) > 0:
            return float(x.replace(',','.'))
    except:
        pass
    return 0.0

def convertint(x):
    if x == None or type(x) == int : return x
    x = str(x).strip()
    try:
        return int(x)
    except:
        return None

def isint(t):
    try:
        int(t)
        return True
    except:
        return False

def intlist( x ):
    return [int(t.strip()) for t in x.split(',') if isint(t.strip())]

def arg_is_true( req, name ):
    return req.args.has_key(name) and req.args[name] == "True"

class EstimationsPage(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)
    def __init__(self):
        pass

    def get_diffs(self, req, old_text, new_text, id):
        diff_style, diff_options, diff_data = get_diff_options(req)
        diff_context = 3
        for option in diff_options:
            if option.startswith('-U'):
                diff_context = int(option[2:])
                break
        if diff_context < 0:
            diff_context = None
        diffs = diff_blocks(old_text.splitlines(), new_text.splitlines(), context=diff_context,
                            tabwidth=2,
                            ignore_blank_lines=True,
                            ignore_case=True,
                            ignore_space_changes=True)
        
        chrome = Chrome(self.env)
        loader = TemplateLoader(chrome.get_all_templates_dirs())
        tmpl = loader.load('diff_div.html')
        
        title = "Estimate:%s Changed" %id
        changes=[{'diffs': diffs, 'props': [],
                  'title': title, 'href': req.href('Estimate', id=id),
                  'new': {'path':title, 'rev':'', 'shortrev': '', 'href': req.href('Estimate', id=id)},
                  'old': {'path':"", 'rev':'', 'shortrev': '', 'href': ''}}]

        data = chrome.populate_data(req,
                                    { 'changes':changes , 'no_id':True, 'diff':diff_data,
                                      'longcol': '', 'shortcol': ''})
        # diffs = diff_blocks("Russ Tyndall", "Russ Foobar Tyndall", context=None, ignore_blank_lines=True, ignore_case=True, ignore_space_changes=True)
        # data = c._default_context_data.copy ()
        diff_data['style']='sidebyside';
        data.update({ 'changes':changes , 'no_id':True, 'diff':diff_data,
                      'longcol': '', 'shortcol': ''})
        stream = tmpl.generate(**data)
        return stream.render()


    def load(self, id, addMessage, data, req, copy=False):
        self.env.log.debug('Loading Estimate: %s' % id)
        try:
            estimate_rs = getEstimateResultSet(self.env, id)
            if estimate_rs:
                if not copy:
                    data["estimate"]["id"] = id
                    data["estimate"]["copyurl"] = req.href.Estimate(copy=id)
                data["estimate"]["rate"] = estimate_rs.value("rate", 0)
                data["estimate"]["tickets"] = estimate_rs.value("tickets", 0)
                data["estimate"]["variability"] = estimate_rs.value("variability", 0)
                data["estimate"]["communication"] = estimate_rs.value("communication", 0)
                data["estimate"]["saveepoch"] = (estimate_rs.value("saveepoch", 0) or 0);
                data["estimate"]["summary"] = (estimate_rs.value("summary", 0));
                rs = getEstimateLineItemsResultSet(self.env, id)
                if rs:
                    excluded = []
                    if copy: excluded=['id', 'estimate_id']
                    data["estimate"]["lineItems"] = rs.json_out(excluded)
            else:
                addMessage('Cant Find Estimate Id: %s' % id)
        except Exception, e:
            addMessage('Invalid Id: %s' % id)
            addMessage('Error: %s' % e)
            
    def notify_old_tickets(self, req, id, addMessage, changer, new_text):
        id = int(id)
        estimate_rs = getEstimateResultSet(self.env, id)
        tickets = estimate_rs.value('tickets', 0)
        old_text = estimate_rs.value('diffcomment', 0)
        tickets = intlist(tickets)
        self.log.debug('About to render the diffs for tickets: %s ' % (tickets, ))
        link = '[/Estimate?id=%s Estimate %s]' % (id,id)
        diffs = self.get_diffs(req, old_text, new_text, id)
        comment = """%s Change Difference:
{{{
#!html
<div class="estimate-diff">
%s
</div>
}}} """ % (link, diffs)
        self.log.debug('Saving estiamte diffs to old tickets: %s \n %s' % (tickets, comment))
        for t in tickets:
            Ticket(self.env,t).save_changes(author=req.authname, comment=comment)
        self.log.debug('Done saving estimate diffs to tickets')
        
    def notify_new_tickets(self, req, id, tickets, addMessage):
        try:
            tag = "[[Estimate(%s)]]" % id
            tickets = intlist(tickets)
            for t in tickets:
                ticket = Ticket (self.env, t)
                if ticket['description'].find (tag) == -1:
                    self.log.debug('Updating Ticket Description : %s'%t)
                    ticket['description'] = ticket['description']+'\n----\n'+tag
                    ticket.save_changes(req.authname, 'added estimate')
            return True
        except Exception, e:
            self.log.error("Error saving new ticket changes: %s" % e)  
            addMessage("Error: %s"  % e)
            return None
                  

    def create_ticket_for_lineitem (self, req, id, addMesage, lineitem, summary=None):
        #skip line items that have a ticket

        if re.search('/ticket/\d+', lineitem.description): return
        compname = 'Estimate-'+str(id)
        if summary: compname = summary
        ensure_component(self.env, compname, req.authname)
        t = Ticket(self.env)
        # try to split on a newline or space that is less than 80 chars into the string
        idx = lineitem.description.find('\n', 0, 80)
        if idx < 0: idx = lineitem.description.find(' ', 45, 80)
        if idx < 0: idx = 45            
        summary = lineitem.description[:idx]
        desc = lineitem.description
        desc += "\n\nFrom [/Estimate?id=%s Created From Estimate %s]" % \
            (lineitem.estimate_id,lineitem.estimate_id)
        t.values['summary'] = summary
        t.values['description'] = desc
        t.values['status'] = 'new'
        t.values['reporter'] = req.authname
        t.values['component'] = compname
        t.values['estimatedhours'] = avg(lineitem.low, lineitem.high)
        t.insert()
        lineitem.description+="\n\nCreated as /ticket/%s" % (t.id, )
        return t
        

    def create_tickets_for_lineitems (self, req, id, addMessage, lineitems, summary=None ):
        return [self.create_ticket_for_lineitem(req, id, addMessage, item, summary)
                for item in lineitems]
            
        
    def line_items_from_args(self, estimate_id ,  args):
        #line items are names like 'nameNum' (so 'description0')
        itemReg = re.compile(r"(\D+)(\d+)")
        lineItems = {}
        
        def lineItemHasher( value, name, id):
            if not lineItems.has_key(id):
                lineItems[id] = EstimateLineItem(id=id, estimate_id=estimate_id)
            setattr(lineItems[id], name, value)
        for item in args.items():
            match = itemReg.match( item[0] )
            if match:
                lineItemHasher( item[1],  *match.groups())
        return lineItems.values()
        
    def save_from_form (self, req, addMessage, estData):

        args = req.args
        tickets = args["tickets"]
        self.log.debug('estimate request-args: %s, %r ' % (args.get("id"), args, ))
        id = args.get("id")
        new_estimate = id == None or id == ''
        if  new_estimate:
            self.log.debug('Saving new estimate')
            sql = estimateInsert
            id = nextEstimateId (self.env)
        else:
            self.log.debug('Saving edited estimate')
            save_diffs = True
            sql = estimateUpdate
        summary = args.get('summary', '').strip()
        save_epoch = to_timestamp(to_datetime(None))
        estimate_args = [args['rate'], args['variability'],
                         args['communication'], tickets,
                         args['comment'], args['diffcomment'], save_epoch, summary, id, ]
        #self.log.debug("Sql:%s\n\nArgs:%s\n\n" % (sql, estimate_args));

        saveEstimate = (sql, estimate_args)

        # we want to delete any rows that were not included in the
        # form request we will not use -1 as a valid id, so this
        # will allow us to use the same sql reguardless of
        # anything else.  Do this as a function so that if we 
        # create tickets, that change is reflected
        lineItems = self.line_items_from_args(id, args)
        ids = ['-1'] 
        newLineItemId = nextEstimateLineItemId (self.env)
        for item in lineItems:
            if item.is_new(): 
                item.id = newLineItemId
                newLineItemId += 1
            else: 
                ids.append(str(item.id))

        def line_item_saver():
            saveLineItems = []
            for item in lineItems:
                saveLineItems.append(item.get_sql_pair())
            remSql = removeLineItemsNotInListSql % ','.join(ids)

            sqls = [(remSql, (id, ))]
            sqls.extend(saveLineItems)
            self.env.log.debug("%r" % sqls)
            dbhelper.execute_in_trans( self.env, *sqls)

        #addMessage("Deleting NonExistant Estimate Rows: %r - %s" % (sql , id))

        sqlToRun=[]
        if new_estimate:
            sqlToRun.append(lambda: self.notify_new_tickets( req, id, tickets, addMessage))
        else:
            # must be before saving the estimate to get diffs right
            sqlToRun.append(lambda: self.notify_old_tickets(req, id, tickets, addMessage,
                                                            args['diffcomment']))
        sqlToRun.append(saveEstimate)
        if arg_is_true(req, "splitIntoTickets"):
            self.log.debug('Setting saveImmediately for estimate %s' % id)
            estData['saveImmediately'] = 'true';
            sqlToRun.append(lambda:self.create_tickets_for_lineitems (req, id, addMessage, lineItems, summary))
        sqlToRun.append(line_item_saver)

        result = dbhelper.execute_in_trans(self.env, *sqlToRun)
        #will be true or Exception
        if result == True:
            addMessage("Estimate Saved!")
            # if we split our preview is out of date, so we will need
            # to save again immediately, so dont do the redirect
            if arg_is_true(req, "splitIntoTickets"): 
                return id 
            if arg_is_true(req, "shouldRedirect"):
                ticket = args["tickets"].split(',')[0]
                req.redirect("%s/%s" % (req.href.ticket(), ticket))
            else:
                req.redirect(req.href.Estimate()+'?id=%s&justsaved=true'%id)
        else:
            addMessage("Failed to save! %s" % result)
   
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if re.search('/Estimate', req.path_info):
            return "Estimate"
        else:
            return ""

    def get_navigation_items(self, req):
        # for tickets with only old estimates on them, we would still like to apply style
        url = req.href.Estimate()
        #style = req.href.chrome('Estimate/estimate.css')
        if req.perm.has_permission("TICKET_MODIFY"):
            yield 'mainnav', "Estimate", \
                  Markup('<a href="%s">%s</a>' %
                         (url , "Estimate"))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/Estimate')
     
    def process_request(self, req):
        if not req.perm.has_permission("TICKET_MODIFY"):
            req.redirect(req.href.wiki())
        messages = []
        def addMessage(s):
            messages.extend([Markup(s)]);
        #addMessage("Post Args: %s"% req.args.items())
        data = {}
        data["estimate"]={
            "href":       req.href.Estimate(),
            "messages":   messages,
            "id": None,
            "lineItems": '[]',
            "tickets": '',
            "saveepoch":0,
            "rate": self.config.get( 'estimator','default_rate') or 200,
            "variability": self.config.get( 'estimator','default_variability') or 1,
            "communication": self.config.get( 'estimator','default_communication') or 1,
            'saveImmediately':'false',
            }
        if req.method == 'POST':
            est_id = self.save_from_form(req, addMessage, data["estimate"])
            # if we didnt redirect, lets make sure all our data gets to the page
            if est_id: self.load(est_id, addMessage, data, req)

        
        def int_arg(name):
            if req.args.has_key(name) and req.args[name].strip() != '':
                return convertint(req.args[name])

        estimateid = int_arg('id')
        copy = int_arg('copy')
        match = re.search('/Estimate/(\d*)', req.path_info)
        
        if not estimateid and match:
            estimateid = match.group(1)
        if estimateid: 
            self.load(estimateid, addMessage, data, req)
        elif copy:
            self.load(copy, addMessage, data, req, copy=True)
            
        if req.args.has_key('justsaved'):
            tickets =  ['<a href="%s/%s">#%s</a>' % (req.href.ticket(), i.strip(), i.strip())
                        for i in data['estimate']['tickets'].split(',')]
            addMessage("Estimate saved and added to tickets: "+(', '.join(tickets)))

        add_script(req, "Estimate/russ-autoresize.jquery.js")
        add_script(req, "Estimate/JSHelper.js")
        add_script(req, "Estimate/Controls.js")
        add_script(req, "Estimate/estimate.js")
        add_script(req, "Estimate/json2.min.js")
        add_stylesheet(req, "Estimate/estimate.css")
        #return 'estimate.cs', 'text/html'
        return 'estimate.html', data, None

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('Estimate', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        genshi templates.
        """
        rtn = [resource_filename(__name__, 'templates')]
        return rtn

class EstimateLineItem (object):
    def __init__(self, id=None, estimate_id=None, description=None,
                 ordinal=None, high=None, low=None):
        for (key, value) in  locals().items():
            if key in ("ordinal", "estimate_id", "id") and value:
                value = convertint(value)
            if key in ("low", "high") and value:
                value = convertfloat(value)
            if key != 'self':
                setattr(self, key, value)
        self._new = self.id >= 400000000 or not self.id

    def is_new (self):
        return self._new

    def get_sql(self):
        if self.is_new():
            return lineItemInsert
        else:
            return lineItemUpdate

    def avg(self):
        return avg(self.low, self.high)

    def to_tuple(self):
        return (self.estimate_id, self.description, self.low, self.high, self.ordinal, self.id)

    def get_sql_pair(self):
        return (self.get_sql(), self.to_tuple())



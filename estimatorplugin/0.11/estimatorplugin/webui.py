import re
import dbhelper
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href
from estimator import *
from trac.ticket import Ticket
import datetime
from trac.web.chrome import Chrome
from trac.util.datefmt import utc, to_timestamp
from trac.versioncontrol.diff import get_diff_options, diff_blocks
from genshi.template import TemplateLoader
from genshi.filters.transform import Transformer
from trac.web.api import ITemplateStreamFilter


# class EstimatorTicketStyleApplication(Component):
#     implements(ITemplateStreamFilter)
    
#     def __init__(self):
#         pass

#     # ITemplateStreamFilter
#     def filter_stream(self, req, method, filename, stream, data):
#         self.log.debug("EstimatorTicketStyleApplication executing") 
#         if not filename == 'ticket.html':
#             self.log.debug("EstimatorTicketStyleApplication not the correct template")
#             return stream
#         #stream = stream | Transformer('//link[ends-with(@href,"trac.css")]').after(
#         stream = stream | Transformer('//link[@href="/projects/test/chrome/common/css/trac.css")]').after(

#             tag.link(type="text/css", rel="stylesheet", 
#                        href=req.href.chrome("common", "css" , "diff.css"))()
#             )
#         return stream


def convertfloat(x):
    "some european countries use , as the decimal separator, never return not a float (0 will be returned if its a bad value)"
    x = str(x).strip()
    try:
        if len(x) > 0:
            return float(x.replace(',','.'))
    except:
        pass
    return 0.0


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


    def load(self, id, addMessage, data):
        try:
            data["estimate"]["id"] = id
            estimate_rs = getEstimateResultSet(self.env, id)
            if estimate_rs:
                data["estimate"]["id"] = id
                data["estimate"]["rate"] = estimate_rs.value("rate", 0)
                data["estimate"]["tickets"] = estimate_rs.value("tickets", 0)
                data["estimate"]["variability"] = estimate_rs.value("variability", 0)
                data["estimate"]["communication"] = estimate_rs.value("communication", 0)
                rs = getEstimateLineItemsResultSet(self.env, id)
                if rs:
                    data["estimate"]["lineItems"] = rs.json_out()
            else:
                addMessage('Cant Find Estimate Id: %s' % id)
        except Exception, e:
            addMessage('Invalid Id: %s' % id)
            addMessage('Error: %s' % e)
            
    def line_item_hash_from_args(self, args):
        #line items are names like 'nameNum' (so 'description0')
        itemReg = re.compile(r"(\D+)(\d+)")
        lineItems = {}
        def lineItemHasher( value, name, id):
            if not lineItems.has_key(id):
                lineItems[id] = {}
            lineItems[id][name] = value
        for item in args.items():
            match = itemReg.match( item[0] )
            if match:
                lineItemHasher( item[1],  *match.groups())
        return lineItems

    def notify_old_tickets(self, req, id, addMessage, changer, new_text):
        #try:
            estimate_rs = getEstimateResultSet(self.env, id)
            tickets = estimate_rs.value('tickets', 0)
            old_text = estimate_rs.value('diffcomment', 0)
            tickets = [int(t.strip()) for t in tickets.split(',')]
            self.log.debug('About to render the diffs for tickets: %s ' % (tickets, ))
            comment = """{{{
#!html
%s
}}} """ % self.get_diffs(req, old_text, new_text, id)
            self.log.debug('Notifying old tickets of estimate change: %s \n %s' % (tickets, comment))
            return [(estimateChangeTicketComment,
                     [t,
                    #there were problems if we update the same tickets comment in the same tick
                    # so we subtract an arbitrary tick to get around this
                      to_timestamp(datetime.datetime.now(utc)) - 1,
                      req.authname,
                      comment
                      ])
                    for t in tickets]
        #except Exception, e:
            self.log.error("Error saving old ticket changes: %s" % e)
            addMessage("Tickets must be numbers")
            return None
        
    def notify_new_tickets(self, req, id, tickets, addMessage):
        try:
            tag = "[[Estimate(%s)]]" % id
            tickets = [int(t.strip()) for t in tickets.split(',')]
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
                  
        
    def save_from_form (self, req, addMessage):
        #try:
            args = req.args
            tickets = args["tickets"]
            if args.has_key("id"):
                id = args['id']
            else:
                id = None
            old_tickets = None
            if id == None or id == '' :
                self.log.debug('Saving new estimate')
                sql = estimateInsert
                id = nextEstimateId (self.env)
            else:
                self.log.debug('Saving edited estimate')
                old_tickets = self.notify_old_tickets(req, id, addMessage, req.authname, args['diffcomment'])
                sql = estimateUpdate
            self.log.debug('Old Tickets to Update: %r' % old_tickets)
            estimate_args = [args['rate'], args['variability'],
                             args['communication'], tickets,
                             args['comment'], args['diffcomment'], id]
            saveEstimate = (sql, estimate_args)
            saveLineItems = []
            newLineItemId = nextEstimateLineItemId (self.env)

            # we want to delete any rows that were not included in the form request
            # we will not use -1 as a valid id, so this will allow us to use the same sql reguardless of anything else
            ids = ['-1'] 
            lineItems = self.line_item_hash_from_args(args).items()
            lineItems.sort()
            for item in lineItems:
                desc, low, high = (item[1]['description'], convertfloat(item[1]['low']), convertfloat(item[1]['high']))
                itemId = item[0]
                if int(itemId) < 400000000:# new ids on the HTML are this number and above
                    ids.append(str(itemId))
                    sql = lineItemUpdate
                else:
                    itemId = newLineItemId
                    newLineItemId += 1
                    sql = lineItemInsert
                itemargs = [id, desc, low, high, itemId]
                saveLineItems.append((sql, itemargs))

            sql = removeLineItemsNotInListSql % ','.join(ids)
            #addMessage("Deleting NonExistant Estimate Rows: %r - %s" % (sql , id))

            sqlToRun = [saveEstimate,
                        (sql, [id]),]
            sqlToRun.extend(saveLineItems)
            if old_tickets:
                sqlToRun.extend(old_tickets)
            
            result = dbhelper.execute_in_trans(self.env, *sqlToRun)
            #will be true or Exception
            if result == True:
                if self.notify_new_tickets( req, id, tickets, addMessage):
                    addMessage("Estimate Saved!")
                    if req.args.has_key('shouldRedirect') and req.args["shouldRedirect"] == "True":
                        ticket = args["tickets"].split(',')[0]
                        req.redirect("%s/%s" % (req.href.ticket(), ticket))
                    else:
                        req.redirect(req.href.Estimate()+'?id=%s&justsaved=true'%id)

            else:
                addMessage("Failed to save! %s" % result)
            
        #except Exception, e:
        #    raise e
        #    addMessage("Error Saving Estimate: %s" % e)
            
   
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
        if req.method == 'POST':
            self.save_from_form(req, addMessage)
        data = {}
        data["estimate"]={
            "href":       req.href.Estimate(),
            "messages":   messages,
            "id": None,
            "lineItems": '[]',
            "tickets": '',
            "rate": self.config.get( 'estimator','default_rate') or 200,
            "variability": self.config.get( 'estimator','default_variability') or 1,
            "communication": self.config.get( 'estimator','default_communication') or 1,
            }
        
        if req.args.has_key('id') and req.args['id'].strip() != '':
            self.load(int(req.args['id']), addMessage, data)
            
        if req.args.has_key('justsaved'):
            tickets =  ['<a href="%s/%s">#%s</a>' % (req.href.ticket(), i.strip(), i.strip())
                        for i in data['estimate']['tickets'].split(',')]
            addMessage("Estimate saved and added to tickets: "+(', '.join(tickets)))

        add_script(req, "Estimate/JSHelper.js")
        add_script(req, "Estimate/Controls.js")
        add_script(req, "Estimate/estimate.js")
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


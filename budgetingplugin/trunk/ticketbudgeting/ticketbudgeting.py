from genshi import HTML
from genshi.builder import tag
from genshi.filters import Transformer
from pkg_resources import resource_filename  # @UnresolvedImport
from trac.config import Option
from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Table, Column
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.translation import domain_functions
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script
import locale
import re
import time



_, tag_, N_, add_domain = domain_functions('ticketbudgeting', '_', 'tag_', 'N_', 'add_domain')

""" budgeting table object \
see trac/db_default.py for samples and trac/db/schema.py for implementation of objects """
BUDGETING_TABLE = Table('budgeting', key=('ticket', 'position'))[
        Column('ticket', type='int'),
        Column('position', type='int'),
        Column('username'),
        Column('type'),
        Column('estimation', type='int64'),
        Column('cost', type='int64'),
        Column('status', type='int'),
        Column('comment')
]

BUDGET_REPORT_ALL_ID = 90

authorizedToModify = ['TICKET_MODIFY', 'TRAC_ADMIN', 'TICKET_BUDGETING_MODIFY']

class Budget:
    """ Container class for budgeting info"""
    _budget_dict = None
    _action = None
    _VALUE_LIST = ['username', 'type', 'estimation', 'cost', 'status', 'comment']

    def __init__(self):
        self._budget_dict = {}

    def set(self, number, value):
        if number == None:
            return

        number = int (number)
        if number > 0 and number < self._VALUE_LIST.__len__() + 1:
            fld = self._VALUE_LIST[number - 1]
            if fld in ('status'):
                try:
                    if value == '':
                        self._budget_dict[fld] = 0
                    else:
                        self._budget_dict[fld] = int (value)
                except Exception, e:
                    fld = '%s.%s' % (BUDGETING_TABLE.name, fld)
                    raise Exception (fld, e)
            elif fld in ('estimation', 'cost'):
                try:
                    if value == '':
                        self._budget_dict[fld] = 0
                    else:
                        try:
                            self._budget_dict[fld] = locale.atof(value)
                        except:
                            self._budget_dict[fld] = float(value)
                except Exception, e:
                    fld = '%s.%s' % (BUDGETING_TABLE.name, fld)
                    raise Exception (fld, e)
            else:
                self._budget_dict[fld] = value

    def do_action(self, env, ticket_id, position):
        if not self._action:
            env.log.warn('no action defined!')
            return

        flds = None
        vals = None
        sql = None
        actionFound = False

        if not ticket_id or not position:
            env.log.error('no ticket-id or position available!')
        elif self._action == 1:
            for key, value in self._budget_dict.iteritems():
                if not flds:    flds = key
                else:           flds += "," + key

                if key in ('username', 'type', 'comment'): value = "'%s'" % value

                if not vals:    vals = str(value)
                else:           vals += ",%s" % value
            actionFound = True
            sql = ("INSERT INTO %s (ticket, position, %s)"
                   " VALUES (%s, %s, %s)" %
                   (BUDGETING_TABLE.name, flds, ticket_id, position, vals))
        elif self._action == 2:
            sql = ''
            i = 0
            for key, value in self._budget_dict.iteritems():
                if i > 0: sql += ","
                if key in ('username', 'type', 'comment'): value = "'%s'" % value
                sql += "%s=%s" % (key, value)
                i += 1
            actionFound = True
            sql = ('UPDATE %s SET %s WHERE ticket=%s AND position=%s' %
                   (BUDGETING_TABLE.name, sql, ticket_id, position))
        elif self._action == 3:
            actionFound = True
            sql = ('DELETE FROM %s WHERE ticket=%s AND position=%s' %
                   (BUDGETING_TABLE.name, ticket_id, position))

        if actionFound:
            env.db_transaction(sql)
            env.log.debug(sql)
        else:
            env.log.error('no appropriate action found! _action is: %s' % self._action)

    def get_values(self):
        return self._budget_dict

    def get_value(self, number):
        if number == None:
            return ""

        number = int (number)
        if number > 0 and number < self._VALUE_LIST.__len__() + 1:
            fld = self._VALUE_LIST[number - 1]
            if fld in ('estimation', 'cost'):
                return locale.format('%.2f', self._budget_dict[fld])
            return self._budget_dict[fld]
        return ""

    def get_action(self):
        return self._action

    def get_action_name(self):
        if self._action == 1:
            return "insert"
        elif self._action == 2:
            return "update"
        elif self._action == 3:
            return "delete"
        else:
            return "unknown"

    def set_as_insert(self):
        self._action = 1

    def set_as_update(self):
        self._action = 2

    def set_as_delete(self):
        self._action = 3

"""
Main Api Module for Plugin ticketbudgeting
"""
class TicketBudgetingView(Component):
    implements(ITemplateProvider, IRequestFilter, ITemplateStreamFilter, ITicketManipulator)
    #  ITicketChangeListener

    _CONFIG_SECTION = 'budgeting-plugin'
    # these options won't be saved to trac.ini
    _types = Option(_CONFIG_SECTION, 'types', 'Implementation|Documentation|Specification|Test',
        """Types of work, which could be selected in select-box.""")
    Option(_CONFIG_SECTION, 'retrieve_users', "permission",
                       'indicates whether users should be retrieved from session or permission table; possible values: permission, session')
    Option(_CONFIG_SECTION, 'exclude_users',
           "'anonymous','authenticated','tracadmin'",
           'list of users, which should be excluded to show in the drop-down list; should be usable as SQL-IN list')
    _type_list = None
    _name_list = None
    _name_list_str = None
    _budgets = None
    _changed_by_author = None



    #===============================================================================
    # see trac/db_default.py, method get_reports (line 175)
    #===============================================================================
#    BUDGET_REPORT_ALL_MINE_ID = self.BUDGET_REPORT_ALL_ID + 1

    BUDGET_REPORTS = [(BUDGET_REPORT_ALL_ID, 'report_title_90', 'report_description_90',
    u"""SELECT t.id, t.summary, t.milestone AS __group__, '../milestone/' || t.milestone AS __grouplink__, 
    t.owner, t.reporter, t.status, t.type, t.priority, t.component,
    count(b.ticket) AS Anz, sum(b.cost) AS Aufwand, sum(b.estimation) AS Schätzung,
    floor(avg(b.status)) || '%' AS "Status", 
    (CASE t.status 
      WHEN 'closed' THEN 'color: #777; background: #ddd; border-color: #ccc;'
      ELSE 
        (CASE sum(b.cost) > sum(b.estimation) WHEN true THEN 'font-weight: bold; background: orange;' END)
    END) AS __style__
    from ticket t
    left join budgeting b ON b.ticket = t.id
    where t.milestone like 
    (CASE $MILESTONE
              WHEN '''' THEN ''%'' 
              ELSE $MILESTONE END) and
    (t.component like (CASE $COMPONENT
              WHEN '' THEN '%' 
              ELSE $COMPONENT END) or t.component is null) and 
    (t.owner like (CASE $OWNER
              WHEN '' THEN $USER 
              ELSE $OWNER END) or t.owner is null or 
     b.username like (CASE $OWNER
              WHEN '' THEN $USER 
              ELSE $OWNER END) )
    group by t.id, t.type, t.priority, t.summary, t.owner, t.reporter, t.component, t.status, t.milestone
    having count(b.ticket) > 0
    order by t.milestone desc, t.status, t.id desc""")
    ]

#===============================================================================
# SELECT t.id, t.summary, t.milestone AS __group__, t.owner, t.reporter, t.type, t.priority, t.component,
#    count(b.ticket) AS Anz, sum(b.cost) AS Aufwand, sum(b.estimation) AS Schätzung, floor(avg(b.status)) AS "Status in %%",
#    (CASE floor(avg(b.status)) = 100
# WHEN true THEN 'font-weight: bold; color: green;'
# ELSE CASE sum(b.cost) > sum(b.estimation)
#              WHEN true THEN 'font-weight: bold; background: orange;'
#              ELSE '' END END) AS __style__
#    from ticket t
#    left join budgeting b ON b.ticket = t.id
#    where t.milestone like
#    (CASE $MILESTONE
#              WHEN '' THEN '%'
#              ELSE $MILESTONE END) and
#    t.component like (CASE $COMPONENT
#              WHEN '' THEN '%'
#              ELSE $COMPONENT END) and
#    (t.owner like (CASE $OWNER
#              WHEN '' THEN $USER
#              ELSE $OWNER END) or
#     b.username like (CASE $OWNER
#              WHEN '' THEN $USER
#              ELSE $OWNER END) )
#    group by t.id, t.type, t.priority, t.summary, t.owner, t.reporter, t.component, t.milestone
#    having count(b.ticket) > 0
# order by t.milestone desc, t.id desc
#===============================================================================


    # Alle Tickets, in der der angemeldete Benutzer beteiligt ist.
#    (BUDGET_REPORT_ALL_MINE_ID, '[budgeting] All tickets, I am involved',
#    """All tickets with budget data, where logged user is involved in budget, or as reporter or owner.
#    """,
#    """SELECT t.id, t.summary, t.owner, t.reporter, t.type, t.priority, t.component,
#    count(b.ticket) AS Anz, sum(b.cost) AS Aufwand, sum(b.estimation) AS Schätzung, avg(b.status) AS Status,
#    t.milestone AS __group__
#    from ticket t
#    left join budgeting b ON b.ticket = t.id
#    where b.username = $USER or t.owner = $USER or t.reporter = $USER
#    group by t.id, t.type, t.priority, t.summary, t.owner, t.reporter, t.component, t.milestone""")

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    def filter_stream(self, req, method, filename, stream, data):
        """ overloaded from ITemplateStreamFilter """
        if filename == 'ticket.html' and data:
            if self._check_init() == False:
                self.create_table()
                self.log.info("table successfully initialized")
            tkt = data['ticket']
            if tkt and tkt.id:
                self._load_budget(tkt.id)
            else:
                self._budgets = {}

            input_html, preview_html = self._get_ticket_html()

            modifyAllowed = False
            for authorizedPerm in authorizedToModify:
                modifyAllowed = modifyAllowed or authorizedPerm in req.perm(tkt.resource)

            if modifyAllowed:
                visibility = ' style="display: none"'
                if self._budgets:
                    visibility = ''

                fieldset = self._get_budget_fieldset() % (visibility, input_html)
                stream |= Transformer('.//fieldset [@id="properties"]').after(HTML(fieldset))



                # Load default values for Type, Estimation, Cost an State from trac.ini
                def_type = self._get_budget_attr('default_type')
                if not def_type:
                    # If the configured default-type is not available, submit -1 ==> first element in type list will be selected
                    def_type = '-1'
                def_est = self._get_budget_attr('default_estimation')
                if not def_est:
                    def_est = '0.0'
                def_cost = self._get_budget_attr('default_cost')
                if not def_cost:
                    def_est = '0.0'
                def_state = self._get_budget_attr('default_state')
                if not def_state:
                    def_state = '0'

                defaults = tag.div(tag.a(self._type_list, id="selectTypes"),
                                    tag.a(self._name_list_str, id="selectNames"),
                                    tag.a(req.authname, id="def_name"),
                                    tag.a(def_type, id="def_type"),
                                    tag.a(def_est, id="def_est"),
                                    tag.a(def_cost, id="def_cost"),
                                    tag.a(def_state, id="def_state"),
                                    style="display: none")

                stream |= Transformer('.//fieldset [@id="budget"]').append(defaults)

            if preview_html:
                fieldset_str = self._get_budget_preview() % preview_html
                stream |= Transformer('//div [@id="content"]//div [@id="ticket"]') \
                            .after(HTML(fieldset_str))
        elif filename == 'milestone_view.html':
            by = 'component'
            if 'by' in req.args:
                by = req.args['by']
            budget_stats, stats_by = self._get_milestone_html(req, by)
            stats_by = "<fieldset><legend>Budget</legend><table>%s</table></fieldset>" % stats_by
            stream |= Transformer('//form[@id="stats"]').append(HTML(stats_by))
            stream |= Transformer('//div[@class="info"]').append(HTML(budget_stats))
        return stream

    def _get_budget_attr(self, name):
        return self.config.get('budgeting-plugin', name)

    def _get_budget_fieldset(self):
        title = _('in hours')
        fieldset = ('<fieldset id="budget">'
                    '<legend>' + _('Budget Estimation') + '</legend>'
                    '<div class="inlinebuttons">'
                    '<label>' + _('Add a new row') + '</label>'
                    '<input type="button" name="addRow" style="margin-left: 5px; border-radius: 1em 1em 1em 1em; font-size: 100%%" onclick="addBudgetRow()" value = "&#x271A;"/>'
                    '</div>'
                       '<span id="hiddenbudgettable"%s>' \
                       '<table>' \
                       '<thead id="budgethead">' \
                       '<tr>' \
                            '<th>' + _('Person') + '</th>' \
                            '<th>' + _('Type') + '</th>' \
                            '<th title="' + title + '">' + _('Estimation') + '</th>' \
                            '<th title="' + title + '">' + _('Cost') + '</th>' \
                            '<th>' + _('State') + '</th>' \
                            '<th style="width:300px">' + _('Comment') + '</th>' \
                        '</tr>' \
                        '</thead>' \
                        '<tbody id="budget_container">%s</tbody>' \
                        '</table>' \
                        '</span>' \
                        '</fieldset>')

        return fieldset

    def _get_budget_preview(self):
        fieldset = '<div id="budgetpreview">' \
                '<h2 class="foldable">' + _('Budget Estimation') + '</h2>' \
                '<table class="listing">' \
                '<thead>' \
                     '<tr>' \
                        '<th style="width:90px">' + _('Person') + '</th>' \
                        '<th style="width:90px">' + _('Type') + '</th>' \
                        '<th style="width:90px">' + _('Estimation') + '</th>' \
                        '<th style="width:90px">' + _('Cost') + '</th>' \
                        '<th style="width:90px">' + _('State') + '</th>' \
                        '<th style="width:300px">' + _('Comment') + '</th>' \
                    '</tr>' \
                    '</thead>' \
                '<tbody id="previewContainer">%s' \
                '</tbody>' \
                '</table>' \
                '</div>'
        return fieldset

    def pre_process_request(self, req, handler):
        """ overridden from IRequestFilter"""
        return handler

    def post_process_request(self, req, template, data, content_type):
        """ overridden from IRequestFilter"""
        if req.path_info.startswith('/newticket') or \
            req.path_info.startswith('/ticket'):
            add_script(req, 'hw/js/budgeting.js')
            if not data:
                return template, data, content_type
            tkt = data['ticket']

            if tkt and tkt.id and Ticket.id_is_valid(tkt.id):  # ticket is ready for saving
                if self._changed_by_author:
                    self._save_budget(tkt)
                self._budgets = None
        return template, data, content_type

    def _get_fields(self, req):
        budget_dict = {}
        budget_obj = None
        # searching budgetfields an send them to db
        for arg in req.args:
            arglist = []
            arglist = arg.split(":")
            if len(arglist) == 3:
                row_no = arglist[1]
                if budget_dict.has_key(row_no):
                    budget_obj = budget_dict[row_no]
                else:
                    budget_obj = Budget()
                    budget_dict[row_no] = budget_obj
                budget_obj.set(arglist[2], req.args.get(arg))

                # New created field, should be insered
                if arglist[0] == "GSfield":
                    budget_obj.set_as_insert()
                elif arglist[0] == "GSDBfield":
                    budget_obj.set_as_update()
                elif arglist[0] == "DELGSDBfield":
                    budget_obj.set_as_delete()

        return budget_dict

    def _get_milestone_html(self, req, group_by):
        html = ''
        stats_by = ''
        ms = req.args['id']

        sql = ("SELECT SUM(b.cost), SUM(b.estimation), AVG(b.status)"
               " FROM budgeting b, ticket t"
               " WHERE b.ticket=t.id AND t.milestone='%s'" % ms)

        try:
            result = self.env.db_query(sql)
            for row in result:
                html = '<dl><dt>' + _('Budget in hours') + ':</dt><dd> </dd>' \
                        '<dt>' + _('Cost') + ': <dd>%.2f</dd></dt>' \
                        '<dt>' + _('Estimation') + ': <dd>%.2f</dd></dt>' \
                        '<dt>' + _('Status') + ': <dd>%.1f%%</dd></dt></dl>'
                html = html % (row[0], row[1], row[2])
                html = self._get_progress_html(row[0], row[1], row[2]) + html
        except Exception, e:
            self.log.error("Error executing SQL Statement \n %s" % e)

        if not group_by:
            return html, stats_by

        sql = ("SELECT t.%s, SUM(b.cost), SUM(b.estimation), AVG(b.status)"
               " FROM budgeting b, ticket t"
               " WHERE b.ticket=t.id AND t.milestone='%s'" \
               " GROUP BY t.%s ORDER BY t.%s" %
               (group_by, ms, group_by, group_by))

        try:
            result = self.env.db_query(sql)
            for row in result:
                status_bar = self._get_progress_html(row[1], row[2], row[3], 75)
                link = req.href.query({'milestone': ms, group_by: row[0]})
                if group_by == 'component':
                    link = req.href.report(BUDGET_REPORT_ALL_ID, {'MILESTONE': ms, 'COMPONENT': row[0], 'OWNER': '%'})

                stats_by += '<tr><th scope="row"><a href="%s">' \
                    '%s</a></th>' % (link, row[0])
                stats_by += '<td>%s</td></tr>' % status_bar
        except Exception, e:
            self.log.error("Error executing SQL Statement \n %s" % e)


        return html, stats_by

    def _get_progress_html(self, cost, estimation, status, width=None):
        ratio = int (0)
        if estimation > 0 and cost:
            leftBarValue = int(round((cost * 100) / estimation, 0))
            ratio = leftBarValue
            rightBarValue = int(round(100 - leftBarValue, 0))
            if(rightBarValue + leftBarValue < 100):
                rightBarValue += 1
            elif leftBarValue > 100:
                leftBarValue = int(100)
                rightBarValue = int(0)
        else:
            leftBarValue = int(0)
            rightBarValue = int(100)

        style_cost = "width: " + str(leftBarValue) + "%"
        style_est = "width: " + str(rightBarValue) + "%"
        title = ' title="' + _('Cost') + ' / ' + _('Estimation') + ': %.1f / %.1f (%.0f %%); ' + _('Status') + ': %.1f%%"'
        title = title % (cost, estimation, ratio, status)
        right_legend = "%.0f %%" % ratio

        if int(status) == 100:
            style_cost += ";background:none repeat scroll 0 0 #3300FF;"
            style_est += ";background:none repeat scroll 0 0 #00BB00;"
        elif ratio > 100:
            style_cost += ";background:none repeat scroll 0 0 #BB0000;"

        status_bar = '<table class="progress"'
        if width:
            status_bar += ' style="width: ' + str(width) + '%"'
            right_legend = "%.0f / %.0f" % (cost, estimation)
        status_bar += '><tr><td class="closed" style="' + style_cost + '">\
               <a' + title + '></a> \
               </td><td style="' + style_est + '" class="open">\
               <a' + title + '></a> \
               </td></tr></table><p class="percent"' + title + '>' + right_legend + '</p>'

        return status_bar

    def _get_ticket_html(self):
        input_html = ''
        preview_html = ''

        if not self._type_list:
            types_str = self.config.get(self._CONFIG_SECTION, 'types')
            self._type_list = re.sub(r'\|', ';', types_str)
            self.log.debug("INIT self._type_list: %s" % self._type_list)
        types = self._type_list.split(';')

        if not self._name_list:
            self._name_list = self.get_user_list()
            self.log.debug("INIT self._name_list: %s" % self._name_list)
            for user in self._name_list:
                if not self._name_list_str:
                    self._name_list_str = str(user)
                else:
                    self._name_list_str += ';' + str(user)

        if self._budgets:
            for pos, budget in self._budgets.iteritems():
                user_options = ''
                type_options = ''
                values = budget.get_values()
                input_html += '<tr id="row:%s">' % pos
                preview_html += '<tr>'
                el_in_list = False

                if self._name_list:
                    for opt in self._name_list:
                        selected = ''
                        if values['username'] == opt:
                            selected = ' selected'
                            el_in_list = True
#                            preview_html += '<td>%s</td>' % opt
                        user_options += '<option%s>%s</option>' % (selected, opt)
                if not el_in_list:
                    user_options += '<option selected>%s</option>' % (values['username'])

                el_in_list = False
                for t in types:
                    selected = ''
                    if values['type'] == t:
                        selected = ' selected'
                        el_in_list = True
#                        preview_html += '<td>%s</td>' % t
                    type_options += '<option%s>%s</option>' % (selected, t)
                if not el_in_list:
                    type_options += '<option selected>%s</option>' % (values['type'])

                input_html += '<td><select name="GSDBfield:%s:1" >%s</select></td>' % (pos, user_options)
                preview_html += '<td>%s</td>' % values['username']
                input_html += '<td><select name="GSDBfield:%s:2">%s</select></td>' % (pos, type_options)
                preview_html += '<td>%s</td>' % values['type']
                size = 10
                for col in range(3, 7):
                    col_val = budget.get_value(col)
                    if col == 6 and col_val:  # comment
                        col_val = col_val.replace('"', "&quot;")
                        size = 60
                    elif not col_val:
                        if col < 6:
                            col_val = '0'
                        else:
                            col_val = ''
                            size = 60
                    input_html += '<td><input size="%s" name="GSDBfield:%s:%s" value="%s"></td>' % (size, pos, col, col_val)
                    preview_html += '<td>%s' % col_val
                    if col == 5:
                        preview_html += '&nbsp;%'
                    preview_html += '</td>'
                input_html += '<td><div class="inlinebuttons"><input type="button" style="border-radius: 1em 1em 1em 1em; font-size: 100%%" name="deleteRow%s" onclick="deleteRow(%s)" value = "&#x2718;"/></div></td>' % (pos, pos)
                input_html += '</tr>'
                preview_html += '</tr>'
        return input_html, preview_html

    def _check_init(self):
        """First setup or initentities deleted
            check initialization, like db setup etc."""
        if (self.config.get(self._CONFIG_SECTION, 'version')):
            self.log.debug ("have local ini, so everything is set")
            return True
        else:
            self.log.debug ("check database")
            try:
                self.env.db_query("SELECT ticket FROM %s" % BUDGETING_TABLE.name)
                self.config.set(self._CONFIG_SECTION, 'version', '1')
                self.config.save()
                self.log.info ("created local ini entries with name budgeting")
                return True
            except Exception:
                self.log.warn ("[_check_init] error while checking database; table 'budgeting' is probably not present")

        return False

    #===============================================================================
    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs
    #===============================================================================
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'htdocs')]

    def get_htdocs_dirs(self):
        return [('hw', resource_filename(__name__, 'htdocs'))]


    def _load_budget(self, ticket_id):
        self._budgets = {}
        if not ticket_id:
            return

        sql = ("SELECT position, username, type, estimation, cost, status, comment"
              " FROM budgeting"
              " WHERE ticket=%s"
              " ORDER BY position" % ticket_id)

        try:
            result = self.env.db_query(sql)
            for row in result:
                budget = Budget()
                for i, col in enumerate(row):
                    if i > 0:
                        budget.set(i, col)
                pos = int (row[0])
                self._budgets[pos] = budget
                self.log.debug("[_load_budget] loaded budget: %s" % budget.get_values())
        except Exception, e:
            self.log.error("Error executing SQL Statement %s \n Error: %s" % (sql, e))

    def _save_budget(self, tkt):
        if self._budgets and tkt and tkt.id:
            user = self._changed_by_author
            self._changed_by_author = None
            for pos, budget in self._budgets.iteritems():
                budget.do_action(self.env, tkt.id, int(pos))
                self.log.debug("saved budget of position: %s" % pos)
            self._log_changes(tkt, user)
            self._budgets = None

    def _log_changes(self, tkt, change_user):
        if not tkt or not tkt.id:
            return
        cur_time = self._get_current_time()

        try:
            with self.env.db_transaction as db:
                for pos, budget in self._budgets.iteritems():
                    action = budget.get_action_name()
                    old_value = ''
                    new_value = ''
                    if action == 'insert':
                        new_value = ("%s, %s: %s" % (budget.get_value(1),
                                                     budget.get_value(2),
                                                     budget.get_value(6)))
                    elif action == 'delete':
                        old_value = ("%s, %s: %s" % (budget.get_value(1),
                                                     budget.get_value(2),
                                                     budget.get_value(6)))
                    elif action == 'update':
                        continue

                    sql = ("INSERT INTO ticket_change(ticket, time, author, field, oldvalue, newvalue)"
                           " VALUES(%s, %s, '%s', 'budgeting.%s', '%s', '%s')"
                            % (tkt.id, cur_time, change_user, pos, old_value, new_value))
                    db(sql)
                    self.log.debug("successfully logged budget, pos %s for ticket %s" % (pos, tkt.id))

        except Exception, ex:
            self.log.error("Error while logging change: %s" % ex)

    def _get_current_time(self):
        return (time.time() - 1) * 1000000

    #===========================================================================
    # If a valid validation check was performed, the budgeting data will
    # be stored to database
    #===========================================================================
    def validate_ticket(self, req, ticket):
        """ overriden from ITicketManipulator """
        errors = []
        try:
            self._budgets = self._get_fields(req)
            self._changed_by_author = req.authname or 'anonymous'
            self.log.info("[validate] budget has changed by author: %s" % self._changed_by_author)
        except Exception, ex:
            self.log.error("Error while validating: %s" % ex)
            fld, e = ex
            errors.append([fld, str(e)])

        return errors


    def create_table(self):
        '''
        Constructor, see trac/postgres_backend.py:95 (method init_db)
        '''
        conn, dummyArgs = DatabaseManager(self.env).get_connector()
        try:
            with self.env.db_transaction as db:
                for stmt in conn.to_sql(BUDGETING_TABLE):
                    if db.schema:
                        stmt = re.sub(r'CREATE TABLE ', 'CREATE TABLE "'
                                      + db.schema + '".', stmt)
                    stmt = re.sub(r'(?i)bigint', 'NUMERIC(10,2)', stmt)
                    stmt += ";"
                    self.log.info("[INIT table] executing sql: %s" % stmt)
                    db(stmt)
                    self.log.info("[INIT table] successfully created table %s" % BUDGETING_TABLE.name)
        except Exception, e:
            self.log.error("[INIT table] Error executing SQL Statement \n %s" % e)
        self.create_reports()

    def create_reports(self):
#        print "[INIT report] create_reports: %s" % self.BUDGET_REPORTS
        for report in self.BUDGET_REPORTS:
            try:
                self.log.info("having myCursor")
                descr = _(report[2])
                self.log.info("descr: %s" % descr)
                descr = re.sub(r"'", "''", descr)
                self.log.info("report[3]: %s" % report[3])
                self.log.info(" VALUES: %s, '%s', '%s'" % (report[0], _(report[1]), report[3]))
                sql = "INSERT INTO report (id, author, title, query, description) "
                sql += " VALUES(%s, null, '%s', '%s', '%s');" % (report[0], _(report[1]), report[3], descr)
                self.log.info("[INIT reports] executing sql: %s" % sql)
                self.env.db_transaction(sql)
                self.log.info("[INIT reports] successfully created report with id %s" % report[0])
            except Exception, e:
                self.log.error("[INIT reports] Error executing SQL Statement \n %s" % e)
                raise e

    def get_col_list(self, ignore_cols=None):
        """ return col list as string; usable for selecting all cols 
        from budgeting table """
        col_list = "";
        i = 0
        for col in BUDGETING_TABLE.columns:
            try:
                if ignore_cols and ignore_cols.index(col.name) > -1: continue
            except: pass

            if (i > 0):
                col_list += ","
            col_list += col.name
            i += 1
        return col_list


    def get_user_list(self):
        sqlResult = []

        sql = "SELECT DISTINCT sid FROM session WHERE authenticated > 0 ORDER BY sid"


        if self.config.get(self._CONFIG_SECTION, 'retrieve_users') == "permission":
            sql = "SELECT DISTINCT username FROM permission"
            if self.config.get(self._CONFIG_SECTION, 'exclude_users'):
                excl_user = self.config.get(self._CONFIG_SECTION, 'exclude_users')
                sql = "%s WHERE username not in (%s)" % (sql, excl_user)
            sql += " ORDER BY username"
        try:
            result = self.env.db_query(sql)
            for row in result:
                sqlResult.append(row[0])
        except Exception, e:
            self.log.error("Error executing SQL Statement \n %s" % e)
        return sqlResult


#===========================================================================
# Class to publish an additional Permission Type
#===========================================================================
class TicketBudgetingPermission(Component):
    implements(IPermissionRequestor)
    """ publicise permission TICKET_BUDGETING_MODIFY """

    definedPermissions = ("TICKET_BUDGETING_MODIFY")
    # IPermissionRequestor
    def get_permission_actions(self):
        yield self.definedPermissions


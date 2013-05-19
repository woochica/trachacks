# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 Aviram C <aviramc@gmail.com>
# Copyright (c) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import random
import string
from collections import defaultdict

from trac.core import implements
from trac.db.api import get_column_names
from trac.web.chrome import ITemplateProvider
from trac.wiki.macros import WikiMacroBase
from trac.ticket.query import Query

import openFlashChart
from openFlashChart_varieties import (
    Bar_Stack, Pie, bar_stack_value, pie_value, x_axis_labels
)
from tracadvparseargs import parseargs

# TODO: Fill more colours
COLOURS = ['#356AA0', '#35a345', '#C711F0', '#C79810', '#D037fC', '#D01F3C', ]


class TicketChartMacro(WikiMacroBase):
    """
    !TicketChartsMacro - display ticket statistics charts.

    Make various types of charts regarding the number of tickets using
    !OpenFlashCharts.

    Chart types:
      * Pie charts.
      * Bar charts.
      * Stacked bar charts.

    The charts are created by the parameters that you give to the macro. See
    the examples below.

    All charts are clickable (see requirements) and will link to the query page
    of the graph.

    Configuration:
      * The following configuration should appear in trac.ini (default values are shown):
    {{{
    [ticket-charts]
    height = 300
    width = 500
    }}}

    Examples:
    {{{
    Number of tickets per milestone:
    [[TicketChart(type = pie, factor = milestone)]]

    Number of tickets per status for milestone4:
    [[TicketChart(type = pie, factor = status, query = milestone="milestone4")]]

    Number of tickets by status and owners:
    [[TicketChart(type = stacked_bars, key = owner, x_axis = status,
    height = 400, width = 600)]]

    Number of tickets by status and owner for milestone1:
    [[TicketChart(type = stacked_bars, key = owner, x_axis = status,
    query = milestone="milestone1",
    title = Tickets by status and owner for milestone1)]]

    Number of tickets by owner and type:
    [[TicketChart(type = stacked_bars, key = type, x_axis = owner)]]

    Number of tickets by status for milestone4:
    [[TicketChart(type = bars, x_axis = status, query = milestone="milestone4",
    title = Tickets by status for milestone4)]]
    }}}
    """
    implements(ITemplateProvider)

    def expand_macro(self, formatter, name, args):
        """Return some output that will be displayed in the Wiki content.

        `name` is the actual name of the macro (no surprise, here it'll be
        `'HelloWorld'`),
        `args` is the text enclosed in parenthesis at the call of the macro.
            Note that if there are ''no'' parenthesis (like in, e.g.
            [[HelloWorld]]), then `args` is `None`.
        """
        return create_graph(formatter.req, formatter.env, args)

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketcharts', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


def _parse_args(args, args_dict = None):
    # The plugin of the args parser in not good enough because it doesn't
    # strip white spaces.
    # Since I didn't want to change the plugin itself, I'll do it here...
    args_list, args_keys = parseargs.parse_args(args, strict=False)

    if args_dict is None:
        stripped_args = {}
    else:
        stripped_args = args_dict     # This way we can use defaultdict
        
    for key, value in args_keys.iteritems():
        stripped_args[key] = value.strip()

    # I don't really need a list for arguments without values, I can make
    # their values None...
    for value in args_list:
        stripped_args[value.strip()] = None

    return stripped_args


def _get_config_variable(env, variable_name, default_value):
    return env.config.get('ticket-charts', variable_name, default_value)


def _get_args_defaults(env, args):
    """
    Fill the args dict with the default values for the keys that don't exist
    """
    defaults = {'height': _get_config_variable(env, 'height', 300),
                'width': _get_config_variable(env, 'width', 500)}
    # Elegant :)
    defaults.update(args)
    return defaults


def _create_chart(title, *elements):
    chart = openFlashChart.template(title)
    for element in elements:
        chart.add_element(element)
    return chart


def _safe_evaluate(string_object, mapping=None, **kw):
    if mapping is None:
        mapping = {}
    return string.Template(string_object).safe_substitute(mapping, **kw)


def _unique_list(iterable):
    return list(set(iterable))


def _javascript_code(code):
    return """<script type="text/javascript">%s</script>""" % (code, )


def _create_javascript_array(array_name, values,
                             function=lambda x: repr(str(x))):
    array_values = ", ".join([function(value) for value in values])
    return "var %s = new Array(%s)" % (array_name, array_values)


def _create_query_object(env, query, required_columns=None):
    """Create a query object from a query string. If query is None, the default
    Query is returned

    :param required_columns: Columns that must be included in the query.
    """
    if query is None:
        return Query(env, cols=required_columns)

    if required_columns is None:
        required_columns = []

    query_object = Query.from_string(env, query)

    # Add the required_columns
    for column in required_columns:
        if column not in query_object.cols:
            query_object.cols.append(column)
            
    return query_object


def _get_query_sql(env, query, required_columns=None):
    query_object = _create_query_object(env, query, required_columns)
    return query_object.get_sql()


def _get_stacked_bar_chart_stats(env, db, key, x_axis, query):
    sql, args = _get_query_sql(env, query, required_columns=[key, x_axis])
    cursor = db.cursor()
    cursor.execute(sql, args)

    query_columns = get_column_names(cursor)

    # Returning all the keys is kind of an optimization (so that we won't look
    # for all keys later on)
    keys = []
    x_axis_field_index = query_columns.index(x_axis)
    # Handle cases in which key is missing. In such cases, we'll form bar charts.
    if key:
        key_field_index = query_columns.index(key)

    # Stacked bar charts are represented by a dict of dicts:
    # {'x_axis_value' : {'key_value' : number_of_tickets}}
    # Regular bar charts will be here the same, but 'key_value' will be
    # replaced with None.
    ticket_stats = defaultdict(lambda: defaultdict(lambda: 0), {})

    for row in cursor:
        if key:
            key_field_value = row[key_field_index]
        else:
            key_field_value = None
        x_axis_field_value = row[x_axis_field_index]
        ticket_stats[x_axis_field_value][key_field_value] += 1
        keys.append(key_field_value)

    return ticket_stats, _unique_list(keys)


def _get_stacked_bar_max_y_value(ticket_stats):
    # x_axis_stats is a dict that its values are the number of tickets for
    # each key
    return max([sum(x_axis_stats.itervalues())
                for x_axis_stats in ticket_stats.itervalues()])


def _remove_query_special_characters(query):
    # The only special characters I know that need to be removed are the quotes.
    # Quotes must be in the query so that the SQL will be executed correctly,
    # but should not exist in links
    special_characters = ["'", '"']
    for special_character in special_characters:
        query = query.replace(special_character, "")
    return query


def _get_query_link(env, query):
    """
    Get a query in a string format, and return a link to the query
    """
    if query:
        query = _remove_query_special_characters(query)
    query_object = _create_query_object(env, query)

    return query_object.get_href(env.href)


def _create_stacked_bar_on_click_html(env, key, x_axis, ticket_stats, query,
                                      function_name):
    """
    Query in the string format
    """
    query_link = _get_query_link(env, query)
    array_name = 'array_%s' % (function_name, )

    if key:
        key_query_string = """+ "&%s=" + text""" % (key, )
    else:
        key_query_string = ''
    
    on_click_code = _safe_evaluate("""
$array_code;

function $function_name(index, text)
{
   document.location = "$query_link&$x_axis=" + $array_name[index] $key_query_string;
}
""", {'array_code': _create_javascript_array(array_name,
                                             ticket_stats.iterkeys()),
      'function_name': function_name,
      'query_link': query_link,
      'x_axis': x_axis,
      'array_name': array_name,
      'key_query_string': key_query_string})
    return _javascript_code(on_click_code)


def _get_stacked_bar_tooltip(key, key_value):
    if key:
        key_string = ' of %s %s' % (key, key_value)
    else:
        key_string = ''
    return '#val# #x_label# tickets%s' % (key_string, )


def _stacked_bars_graph(env, db, key, x_axis, query=None, title=None):
    ticket_stats, keys = _get_stacked_bar_chart_stats(env, db, key, x_axis,
                                                      query)

    plot = Bar_Stack()

    # Add the keys to the plot
    key_colours = {}
    for i, key_value in enumerate(keys):
        key_colours[key_value] = COLOURS[i]
        if key:
            plot.append_keys(COLOURS[i], key_value, 13)

    for x_axis_value, tickets_per_key in ticket_stats.iteritems():
        stack = []
        for i, (key_value, number_of_tickets) in enumerate(tickets_per_key.iteritems()):
            stack.append(bar_stack_value(number_of_tickets, key_colours[key_value], _get_stacked_bar_tooltip(key, key_value)))
        plot.append_stack(stack)

    chart_div_id = _create_chart_div_id()
    on_click_function_name = 'on_click_%s' % (chart_div_id, )
    plot['on-click'] = on_click_function_name
    plot['on-click-text'] = '#key#'

    if title is None:
        key_string = ''
        if key:
            key_string = ' and %s' % (key, )
        title = 'Tickets by %s%s' % (x_axis, key_string)
    chart = _create_chart(title, plot)
    chart.set_x_axis(labels = x_axis_labels(labels=ticket_stats.keys(), size=13))
    chart.set_y_axis(min = 0, max = _get_stacked_bar_max_y_value(ticket_stats))

    return chart, chart_div_id, \
           _create_stacked_bar_on_click_html(env, key, x_axis, ticket_stats,
                                             query, on_click_function_name)


def stacked_bars_graph(env, db, args):
    # Using **args here would be useful, but I want to be more precise
    return _stacked_bars_graph(env, db, key=args['key'], x_axis=args['x_axis'],
                               query=args.get('query'),
                               title=args.get('title'))


def bars_graph(env, db, args):
    # I don't want code repetition, so we'll simply use stacked bars chart
    # without keys. This is kind of a hack, but it's better than copy-paste.
    return _stacked_bars_graph(env, db, key=None, x_axis=args['x_axis'],
                               query=args.get('query'),
                               title=args.get('title'))


def _get_pie_graph_stats(env, db, factor, query=None):
    """
    Return a dict in which the keys are the factors and the values are the
    number of tickets of each factor.
    Example:

    >>> _get_pie_graph_stats(env, db, 'milestone')
    {'milestone1' : 20,
     'milestone2' : 12,
    }
    """
    sql, args = _get_query_sql(env, query, required_columns=[factor, ])
    cursor = db.cursor()
    cursor.execute(sql, args)

    query_columns = get_column_names(cursor)
    factor_index = query_columns.index(factor)

    ticket_stats = defaultdict(lambda: 0)
    for row in cursor:
        factor_value = row[factor_index]
        ticket_stats[factor_value] += 1

    return ticket_stats


def _create_pie_graph_on_click_html(env, ticket_stats, factor, query,
                                    function_name):
    query_link = _get_query_link(env, query)
    array_name = 'array_%s' % (function_name, )
    
    on_click_code = _safe_evaluate("""
$array_code;

function $function_name(index)
{
    document.location = '$query_link&$factor=' + $array_name[index]
}
""", {'array_code': _create_javascript_array(array_name,
                                             ticket_stats.iterkeys()),
      'function_name': function_name,
      'query_link': query_link,
      'factor': factor,
      'array_name': array_name})

    return _javascript_code(on_click_code)


def _pie_graph(env, db, factor, query=None, title=None):
    """
    Create a pie graph of the number of tickets as a function of the factor.
    factor is a name of a field by which the tickets are counted.
    query can be None or any Trac query by which the data will be collected.
    """
    ticket_stats = _get_pie_graph_stats(env, db, factor, query)

    pie_values = []
    for factor_value, number_of_tickets in ticket_stats.iteritems():
        pie_values.append(pie_value(number_of_tickets,
                                    label=(factor_value, None, '13'),
                                    ))

    plot = Pie(start_angle=35, animate=True, values=pie_values,
               colours=COLOURS, label_colour='#432BAF')
    plot.set_tooltip('#label# - #val# tickets (#percent#)')

    chart_div_id = _create_chart_div_id()
    on_click_function_name = 'on_click_%s' % (chart_div_id, )
    plot.set_on_click(on_click_function_name)

    if not title:
        title = "Tickets per %s" % (factor, )

    chart = _create_chart(title, plot)

    on_click_html = _create_pie_graph_on_click_html(env, ticket_stats, factor,
                                                    query,
                                                    on_click_function_name)

    return chart, chart_div_id, on_click_html


def pie_graph(env, db, args):
    return _pie_graph(env, db, args['factor'], query=args.get('query'),
                      title=args.get('title'))


def create_graph(req, env, args):
    db = env.get_db_cnx()

    args = _parse_args(args)
    args = _get_args_defaults(env, args)
    
    chart_creation = {'stacked_bars': stacked_bars_graph,
                      'bars': bars_graph,
                      'pie': pie_graph}

    chart, chart_div_id, additional_html = chart_creation[args['type']](env,
                                                                        db,
                                                                        args)

    # Using OFCDZ in order to enable links in Bar Stack chart.
    return additional_html + \
           _get_chart_html(chart, chart_div_id,
                           req.href.chrome(),
                           height=args['height'], width=args['width'])


def _get_random_string(length):
    return ''.join([random.choice(string.letters + string.digits)
                    for i in xrange(length)])


def _create_chart_div_id():
    div_id_prefix = 'chart_'

    random_string = _get_random_string(10)

    return div_id_prefix + random_string


def _get_chart_html(chart_object, chart_div_id, htdocs_dir, height=300,
                    width=500):
    get_data_function = "get_%s" % (chart_div_id, )
    chart_html = """
<script type="text/javascript" src="$htdocs_dir/ticketcharts/js/swfobject.js">
</script>
<script type="text/javascript" src="$htdocs_dir/ticketcharts/js/json/json2.js">
</script>
<script type="text/javascript">
swfobject.embedSWF("$htdocs_dir/ticketcharts/open-flash-chart.swf",
                   "$chart_div_id", "$width", "$height", "9.0.0", "blah.swf",
                   {"get-data" : "$get_data_function"});
</script>

<script type="text/javascript">

function $get_data_function()
{
    return JSON.stringify($chart_data);
}

</script>

<div id="$chart_div_id"></div>
"""
    return _safe_evaluate(chart_html, chart_div_id=chart_div_id,
                          htdocs_dir=htdocs_dir,
                          width=width, height=height,
                          chart_data=chart_object.encode(),
                          get_data_function=get_data_function)

from trac.wiki.macros import WikiMacroBase
from trac.util.html import Markup

from GChartWrapper import GChart as GoogleChart

NON_API_KEYS = ['type', 'query', 'columns']

class GChart(WikiMacroBase):
    """Create a chart using the Google Chart API.
     
    The GChart macro is initialised with keyword arguments much like a Python
    function. The two required arguments are 'query' (a SQL query) and 'type'
    (the chart type).  
    
    You can describe your columns by passing a 'columns' list like this:

    {{{
	columns = [('x', 'labels'), ('y', 'scaled', 0, 150)]
    }}}

    If you pass this, you must describe all columns in the output. The first
    tuple parameter is the axis. The second is the type, which can be one of:

     * labels - this column contains data labels for this axis
     * percentage - this column contains unscaled data (range 0..100)
     * scaled - this column contains scaled data (arbitrary values)
    
    If the type is 'scaled' you can also add arguments for the min and max
    values to scale to. Pass None to use the min/max of the range.

    Other arguments are passed to the GChartWrapper plugin constructor.
     
    When rendered, the query will be executed. Each column will be sent to the
    Google Chart API as a dataset.
     
    Examples:
    {{{
        [[GChart(query="SELECT id FROM ticket", type="line")]]
	[[GChart(query='SELECT id, time FROM ticket', type='line', \
                 chtt='My chart', columns=[('x', 'labels'), ('y', 'scaled')])]]
    }}}
    """
    
    def render_macro(self, req, name, content):
        # XXX: This is a big security hole. Need to replace this with something that
        # only accepts simple key/value pairs.
        options = eval("dict(%s)" % content)
        
        query = options.get('query', None)
        ctype = options.get('type', None)
	columns = options.get('columns', None)

        if query is None or ctype is None:
            raise ValueError("Chart 'type' and 'query' parameters are required")
        
        for key in NON_API_KEYS:
            if key in options:
                del options[key]

        datasets = {}
	scales = {}
	labels = {}

	if columns is not None:
	   for idx, val in enumerate(columns):
		if len(val) >= 2:
		    if val[1] == 'labels':
			labels[idx] = []
		    elif val[1] in ('percentage', 'scaled'):
			datasets[idx] = []
			scales[idx] = (0,0)
 
	db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(query)

	col_count = 0
	if columns is not None:
	    col_count = len(columns)

	# Collect label, scale and dataset data
        for row in cursor:
	    if not col_count:
		col_count = len(row)
		if columns is None:
		    columns = []
		    for idx in range(col_count):
			columns.append((None, 'percentage'))
			datasets[idx] = []
			scales[idx] = (0,0)
		elif len(columns) != col_count:
		    raise KeyError("Table has %d columns, but 'columns' parameter has %d items" % \
		   		    (col_count, len(columns),))

	    for idx, col in enumerate(row):
		if idx in labels:
		    labels[idx].append(col)
		elif idx in datasets:
		    try:
			col_value = float(col)
		    except (TypeError, ValueError):
			continue
		    
		    datasets[idx].append(col_value)
		    scales[idx] = (min(scales[idx][0], col_value),
				   max(scales[idx][1], col_value),)

	dense_dataset = []
	dataset_to_idx = {}

	idx_to_axis = {}
	axis_to_idx = {}

	axis_types = []  # x, x, y - in order
	scaled_axes = {} # idx -> min/max for that scale

	current_dataset = 0
	current_axis = 0

	for idx, col in enumerate(columns):
	    if len(col) >= 1 and col[0]:
		idx_to_axis[idx] = current_axis
		axis_to_idx[current_axis] = idx
		axis_types.append(col[0])
		current_axis += 1

	    if len(col) >= 2 and col[1] == 'scaled':
		scale_min = len(col) >= 3 and col[2] or scales[idx][0]
		scale_max = len(col) >= 4 and col[3] or scales[idx][1]
		scaled_axes[idx] = (scale_min, scale_max,)

	    if idx in datasets:
		dataset_to_idx[current_dataset] = idx
		dense_dataset.append(datasets[idx])
		current_dataset += 1

	# Add axes
	if 'chxt' not in options:
	    if axis_types:
		options['chxt'] = ','.join(axis_types)

	# Add axis labels
	if 'chxl' not in options:
	    label_data = []
	    for idx, values in sorted(labels.items()):
		if idx not in idx_to_axis:
		    continue
		label_data.append('%d:|%s' % (idx_to_axis[idx], '|'.join(values),))
	    if label_data:
		options['chxl'] = '|'.join(label_data)

	# Add scale range axes
	if 'chxr' not in options:
	    range_triples = []
	    for idx, (scale_min, scale_max) in sorted(scaled_axes.items()):
		if idx not in idx_to_axis:
		    continue
		range_triples.append('%d,%.1f,%.1f' % (idx_to_axis[idx], scale_min, scale_max,))
	    if range_triples:
		options['chxr'] = '|'.join(range_triples)    
    
	# Add data scaling
	if 'chds' not in options and scaled_axes:
	    scale_data = []
	    for cnt in range(len(dense_dataset)):
		idx = dataset_to_idx[cnt]
		scale_item = ','
		if idx in scaled_axes:
		    scale_min, scale_max = scaled_axes[idx]
		    scale_item = '%.1f,%.1f' % (scale_min, scale_max)
		scale_data.append(scale_item)
	    if scale_data:
		options['chds'] = ','.join(scale_data)

        chart = GoogleChart(ctype=ctype, dataset=dense_dataset, **options)
        return Markup(chart.img())

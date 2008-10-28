from trac.wiki.macros import WikiMacroBase
from trac.util.html import Markup

from GChartWrapper import GChart as GoogleChart

NON_API_KEYS = ['type', 'query', 'tuples']

class GChart(WikiMacroBase):
    """Create a chart using the Google Chart API.
     
    The GChart macro is initialised with keyword arguments much like a Python
    function. The two required arguments are 'query' (a SQL query) and 'type'
    (the chart type).  In addition, you can pass 'tuples=True' to have columns
    be sent as tuples, with each row a dataset. Otherwise, each full column will
    be used as one dataset.
    
    Other arguments are passed to the GChartWrapper plugin constructor.
     
    When rendered, the query will be executed. Each column will be sent to the
    Google Chart API as a dataset.
     
    Examples:
    {{{
        [[GChart(query="SELECT id FROM ticket", type="line")]]
        [[GChart(query="SELECT id, time FROM ticket", type="line", tuples=True)]]
    }}}
    """
    
    def render_macro(self, req, name, content):
        
        # XXX: This is a big security hole. Need to replace this with something that
        # only accepts simple key/value pairs.
        options = eval("dict(%s)" % content)
        
        query = options.get('query', None)
        ctype = options.get('type', None)
        tuples = options.get('tuples', False)
        
        if query is None or ctype is None:
            raise ValueError("Chart 'type' and 'query' parameters are required")
        
        for key in NON_API_KEYS:
            if key in options:
                del options[key]
        
        
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(query)
        
        dataset = []
        
        for row in cursor:
            row_data = []
            for col in row:
                try:
                    row_data.append(float(col))
                except ValueError:
                    pass
            if not row_data:
                continue
            if tuples:
                dataset.append(row_data)
            else:
                for idx, data in enumerate(row_data):
                    if idx < len(dataset):
                        dataset[idx].append(data)
                    else:
                        dataset.append([data])
        
        chart = GoogleChart(ctype=ctype, dataset=dataset, **options)
        return Markup(chart.img())

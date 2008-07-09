<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<style type="text/css">
#chart { height: 500px }
</style>

<script type="text/javascript" src="http://yui.yahooapis.com/2.5.2/build/yahoo-dom-event/yahoo-dom-event.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.5.2/build/element/element-beta-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.5.2/build/datasource/datasource-beta-min.js"></script>
<script type="text/javascript" src="http://yui.yahooapis.com/2.5.2/build/json/json-min.js"></script>
<!-- OPTIONAL: Connection (enables XHR) -->
<script type="text/javascript" src="http://yui.yahooapis.com/2.5.2/build/connection/connection-min.js"></script>
<!-- Source files -->
<script type="text/javascript" src="http://yui.yahooapis.com/2.5.2/build/charts/charts-experimental-min.js"></script>
<p>
<span class="chart_title">
	<h1>Ticket Statistics</h1>
</span>
<div id="chart"></div>
<form action="" method="post" id="dt_frm">
	<label for="start_date">Start Date: </label>
		<input type="text" name="start_date" id="start_date" value="<?cs var:start_date ?>">
	<label for="end_date">End Date: </label>
		<input type="text" name="end_date" id="end_date" value="<?cs var:end_date ?>">
	<label for="resolution">Resolution: </label>
		<input type="text" name="resolution" id="resolution" value="<?cs var:resolution ?>">
	<input type="submit" value="Update Chart">	
</form>

<script type = "text/javascript">
YAHOO.widget.Chart.SWFURL = "http://yui.yahooapis.com/2.5.2/build/charts/assets/charts.swf";


var mychartdata = 
[
//
	<?cs each:item = ticket_data.chart_data ?>{ date: "<?cs var:item.date ?>", new_tickets: <?cs var:item.new ?>, closed: <?cs var:item.closed ?>, open: <?cs var:item.open ?> },
	<?cs /each ?>
];

var myDataSource = new YAHOO.util.DataSource( mychartdata );
myDataSource.responseType = YAHOO.util.DataSource.TYPE_JSARRAY;
myDataSource.responseSchema =
{
	fields: [ "date", "new_tickets", "open", "closed" ]
};

var seriesDef =
[
	{ displayName: "New Tickets", yField: "new_tickets", style: {color: 0xff0000, size: 40} },
	{ displayName: "Closed Tickets", yField: "closed", style: {color: 0x00ff00, size:40} },
	{ type: "line", displayName: "Open Tickets", yField: "open", style: {color: 0x0000ff} },
];

var numtixAxis = new YAHOO.widget.NumericAxis();
numtixAxis.minimum = 0

YAHOO.example.getDataTipText = function( item, index, series )
{
	var toolTipText = series.displayName + " for " + item.date;
	toolTipText += "\n" + item[series.yField] ;
	return toolTipText;
}

var mychart = new YAHOO.widget.ColumnChart( "chart", myDataSource,
{
	xField: "date",
	series: seriesDef,
	yAxis: numtixAxis,
	dataTipFunction: YAHOO.example.getDataTipText,
	style: {legend: {display: "bottom"}},
});


</script>
<?cs include "footer.cs" ?>

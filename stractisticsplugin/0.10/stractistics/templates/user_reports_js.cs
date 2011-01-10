<!--
Javascript for user reports.
-->

<script type="text/javascript">
function loadUserCharts()
{
	loadSVNActivityChart();
	loadWikiActivityChart();
	loadTicketActivityChart();
}
</script>


<script type="text/javascript">
	
    
	//-------------------------------------
	//-------------------------------------
	//In order to fully understand this function, take a look at the HDF.
	function loadSVNActivityChart() {

	//We pick up the data from the HDF
		
	var y_numSteps = <?cs var:svn_activity.chart_info.y_steps?>;
	var x_orientation = <?cs var:svn_activity.chart_info.x_orientation?>;
	var x_font_size = <?cs var:svn_activity.chart_info.x_font_size ?>;
	var chart_width = '<?cs var:svn_activity.chart_info.width ?>';
	var chart_height = '<?cs var:svn_activity.chart_info.height ?>';
	var num_results = <?cs var:svn_activity.chart_info.data_size ?>;
	var x_font_color = '<?cs var:svn_activity.chart_info.x_font_color?>';
	var chart_type = '<?cs var:svn_activity.chart_info.type?>';
	var chart_title = '<?cs var:svn_activity.chart_info.title ?>';
	var bg_color = '<?cs var:svn_activity.chart_info.bg_color ?>';
	var x_axis_color = '<?cs var:svn_activity.chart_info.x_axis_color ?>';
	var y_axis_color = '<?cs var:svn_activity.chart_info.y_axis_color ?>';
	var x_grid_color = '<?cs var:svn_activity.chart_info.x_grid_color ?>';
	var y_grid_color = '<?cs var:svn_activity.chart_info.y_grid_color ?>';
	var tool_tip = '<?cs var:svn_activity.chart_info.tool_tip?>';
	var x_legend = '<?cs var:svn_activity.chart_info.x_legend?>';
	var y_legend = '<?cs var:svn_activity.chart_info.y_legend?>';

	var colorsArray = new Array();
	var index = 0;
	<?cs each:color = svn_activity.chart_info.colors ?>
		colorsArray[index] = '<?cs var:color ?>';
		index++;
	<?cs /each ?>

	try {
		var o = new OFC('<?cs var:svn_activity.chart_info.name ?>');
	} catch (error) {
		setTimeout("loadSVNActivityChart()",100);
		return;
	}

	o.setXLabelStyle(x_font_size,x_font_color,x_orientation);
	o.set('bg_colour',bg_color);
	o.set('x_axis_colour',x_axis_color);
	o.set('y_axis_colour',y_axis_color);
	o.set('x_grid_colour',x_grid_color);
	o.set('y_grid_colour',y_grid_color);
	o.setLegend('x', x_legend);
	o.setLegend('y', y_legend);

	if (tool_tip !=''){ 
		o.set('tool_tip',tool_tip);
	}
	
	o.emptyDataList();
	o.xlabels = null;

	//Labels for x values
	var xArray = new Array();
	var numLabelValues = 0;
	<?cs each:label = svn_activity.chart_info.x_labels ?>
		xArray[numLabelValues] = '<?cs var:label ?>';
		numLabelValues++;
	<?cs /each ?>
	o.xlabels = xArray;
	
	
	var maxY = 0;
	var numArrays = 0;
	var data_array = new Array(); 
	var keys_array = new Array(); 
	<?cs each:array = svn_activity.chart_info.data ?>
		keys_array[numArrays] = '<?cs var:array.author ?>';
		data_array[numArrays] = new Array();
		var data_number = 0;
		<?cs each:data_elem = array.info ?>
			data_array[numArrays][data_number] = <?cs var:data_elem ?>;
			if ( data_array[numArrays][data_number] > maxY ){
				maxY = data_array[numArrays][data_number];
			}
			data_number++;
		<?cs /each ?>
		numArrays++;
	<?cs /each ?>

	o.set('y_max',Math.ceil(maxY/y_numSteps)*y_numSteps);
	o.setTitle(chart_title);
	
	var myData = new Array(numArrays);
	for (ii = 0; ii < numArrays; ii++){
		myData[ii] = new Line();
		myData[ii].values = data_array[ii];
		myData[ii].setKey(keys_array[ii],10);
		myData[ii].changeColors([colorsArray[ii%colorsArray.length]]);	
		o.addData(myData[ii]);
	}
    o.redraw();
}
</script>


<!-- For displaying Wiki activity chart -->
<script>
function loadWikiActivityChart(){

	var y_numSteps = <?cs var:wiki_activity.chart_info.y_steps?>;
	var x_orientation = <?cs var:wiki_activity.chart_info.x_orientation?>;
	var x_font_size = <?cs var:wiki_activity.chart_info.x_font_size ?>;
	var chart_width = '<?cs var:wiki_activity.chart_info.width ?>';
	var chart_height = '<?cs var:wiki_activity.chart_info.height ?>';
	var num_results = <?cs var:wiki_activity.chart_info.data_size ?>;
	var x_font_color = '<?cs var:wiki_activity.chart_info.x_font_color?>';
	var chart_type = '<?cs var:wiki_activity.chart_info.type?>';
	var chart_title = '<?cs var:wiki_activity.chart_info.title ?>';
	var bg_color = '<?cs var:wiki_activity.chart_info.bg_color ?>';
	var x_axis_color = '<?cs var:wiki_activity.chart_info.x_axis_color ?>';
	var y_axis_color = '<?cs var:wiki_activity.chart_info.y_axis_color ?>';
	var x_grid_color = '<?cs var:wiki_activity.chart_info.x_grid_color ?>';
	var y_grid_color = '<?cs var:wiki_activity.chart_info.y_grid_color ?>';
	var tool_tip = '<?cs var:wiki_activity.chart_info.tool_tip?>';
	var x_legend = '<?cs var:wiki_activity.chart_info.x_legend?>';
	var y_legend = '<?cs var:wiki_activity.chart_info.y_legend?>';
	
	var colorsArray = new Array();
	var index = 0;
	<?cs each:color = wiki_activity.chart_info.colors ?>
		colorsArray[index] = '<?cs var:color ?>';
		index++;
	<?cs /each ?>

	try {
		var o = new OFC('<?cs var:wiki_activity.chart_info.name ?>');
	} catch (error) {
		setTimeout("loadWikiActivityChart()",100);
		return;
	}	
	
	o.setXLabelStyle(x_font_size,x_font_color,x_orientation);
	o.set('bg_colour',bg_color);
	o.set('x_axis_colour',x_axis_color);
	o.set('y_axis_colour',y_axis_color);
	o.set('x_grid_colour',x_grid_color);
	o.set('y_grid_colour',y_grid_color);
	o.setLegend('x', x_legend);
	o.setLegend('y', y_legend);

	if (tool_tip !=''){ 
		o.set('tool_tip',tool_tip);
	}

	o.emptyDataList();
	o.xlabels = null;

	//Labels for x values
	var xArray = new Array();
	var numLabelValues = 0;
	<?cs each:label = wiki_activity.chart_info.x_labels ?>
		xArray[numLabelValues] = '<?cs var:label ?>';
		numLabelValues++;
	<?cs /each ?>
	o.xlabels = xArray;
	

	var maxY = 0;
	var numArrays = 0;
	var data_array = new Array(); 
	var keys_array = new Array(); 
	<?cs each:array = wiki_activity.chart_info.data ?>
		keys_array[numArrays] = '<?cs name:array ?>';
		data_array[numArrays] = new Array();
		var data_number = 0;
		<?cs each:data_elem = array ?>
			data_array[numArrays][data_number] = <?cs var:data_elem ?>;
			if ( data_array[numArrays][data_number] > maxY ){
				maxY = data_array[numArrays][data_number];
			}
			data_number++;
		<?cs /each ?>
		numArrays++;
	<?cs /each ?>

	o.set('y_max',Math.ceil(maxY/y_numSteps)*y_numSteps);
	o.setTitle(chart_title);
	
	var myData = new Array(numArrays);
	for (ii = 0; ii < numArrays; ii++){
		myData[ii] = new Line();
		myData[ii].values = data_array[ii];
		myData[ii].setKey(keys_array[ii],10);
		myData[ii].changeColors([colorsArray[ii%colorsArray.length]]);	
		o.addData(myData[ii]);
	}
        o.redraw();
}
</script>



<!-- For displaying Ticket activity chart -->
<script>
function loadTicketActivityChart(){

	var y_numSteps = <?cs var:ticket_activity.chart_info.y_steps?>;
	var x_orientation = <?cs var:ticket_activity.chart_info.x_orientation?>;
	var x_font_size = <?cs var:ticket_activity.chart_info.x_font_size ?>;
	var chart_width = '<?cs var:ticket_activity.chart_info.width ?>';
	var chart_height = '<?cs var:ticket_activity.chart_info.height ?>';
	var num_results = <?cs var:ticket_activity.chart_info.data_size ?>;
	var x_font_color = '<?cs var:ticket_activity.chart_info.x_font_color?>';
	var chart_type = '<?cs var:ticket_activity.chart_info.type?>';
	var chart_title = '<?cs var:ticket_activity.chart_info.title ?>';
	var bg_color = '<?cs var:ticket_activity.chart_info.bg_color ?>';
	var x_axis_color = '<?cs var:ticket_activity.chart_info.x_axis_color ?>';
	var y_axis_color = '<?cs var:ticket_activity.chart_info.y_axis_color ?>';
	var x_grid_color = '<?cs var:ticket_activity.chart_info.x_grid_color ?>';
	var y_grid_color = '<?cs var:ticket_activity.chart_info.y_grid_color ?>';
	var tool_tip = '<?cs var:ticket_activity.chart_info.tool_tip?>';
	var x_legend = '<?cs var:ticket_activity.chart_info.x_legend?>';
	var y_legend = '<?cs var:ticket_activity.chart_info.y_legend?>';
	
	var colorsArray = new Array();
	var index = 0;
	<?cs each:color = ticket_activity.chart_info.colors ?>
		colorsArray[index] = '<?cs var:color ?>';
		index++;
	<?cs /each ?>

	try {
		var o = new OFC('<?cs var:ticket_activity.chart_info.name ?>');
	} catch (error) {
		setTimeout("loadTicketActivityChart()",100);
		return;
	}	
	
	o.setXLabelStyle(x_font_size,x_font_color,x_orientation);
	o.set('bg_colour',bg_color);
	o.set('x_axis_colour',x_axis_color);
	o.set('y_axis_colour',y_axis_color);
	o.set('x_grid_colour',x_grid_color);
	o.set('y_grid_colour',y_grid_color);
	o.setLegend('x', x_legend);
	o.setLegend('y', y_legend);

	if (tool_tip !=''){ 
		o.set('tool_tip',tool_tip);
	}

	o.emptyDataList();
	o.xlabels = null;

	//Labels for x values
	var xArray = new Array();
	var numLabelValues = 0;
	<?cs each:label = ticket_activity.chart_info.x_labels ?>
		xArray[numLabelValues] = '<?cs var:label ?>';
		numLabelValues++;
	<?cs /each ?>
	o.xlabels = xArray;
	

	var maxY = 0;
	var numArrays = 0;
	var data_array = new Array(); 
	var keys_array = new Array(); 
	<?cs each:array = ticket_activity.chart_info.data ?>
		keys_array[numArrays] = '<?cs name:array ?>';
		data_array[numArrays] = new Array();
		var data_number = 0;
		<?cs each:data_elem = array ?>
			data_array[numArrays][data_number] = <?cs var:data_elem ?>;
			if ( data_array[numArrays][data_number] > maxY ){
				maxY = data_array[numArrays][data_number];
			}
			data_number++;
		<?cs /each ?>
		numArrays++;
	<?cs /each ?>

	o.set('y_max',Math.ceil(maxY/y_numSteps)*y_numSteps);
	o.setTitle(chart_title);
	
	var myData = new Array(numArrays);
	for (ii = 0; ii < numArrays; ii++){
		myData[ii] = new Line();
		myData[ii].values = data_array[ii];
		myData[ii].setKey(keys_array[ii],10);
		myData[ii].changeColors([colorsArray[ii%colorsArray.length]]);	
		o.addData(myData[ii]);
	}
        o.redraw();
}
</script>


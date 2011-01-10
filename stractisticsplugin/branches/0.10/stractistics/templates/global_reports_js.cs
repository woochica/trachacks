<!--
Javascript for global reports.
-->

<script type="text/javascript">
function loadCharts()
{
	loadRepoActivityChart();
	loadTicketActivityChart();
	loadWikiActivityChart();
}
</script>


<script type="text/javascript">
	
    
	//-------------------------------------
	//-------------------------------------
	//In order to fully understand this function, take a look at the HDF.
	function loadRepoActivityChart() {

	//We pick up the data from the HDF
		
	var y_numSteps = <?cs var:repository_activity.chart_info.y_steps?>;
	var x_orientation = <?cs var:repository_activity.chart_info.x_orientation?>;
	var x_font_size = <?cs var:repository_activity.chart_info.x_font_size ?>;
	var chart_width = '<?cs var:repository_activity.chart_info.width ?>';
	var chart_height = '<?cs var:repository_activity.chart_info.height ?>';
	var num_results = <?cs var:repository_activity.chart_info.data_size ?>;
	var x_font_color = '<?cs var:repository_activity.chart_info.x_font_color?>';
	var chart_type = '<?cs var:repository_activity.chart_info.type?>';
	var chart_title = '<?cs var:repository_activity.chart_info.title ?>';
	var bg_color = '<?cs var:repository_activity.chart_info.bg_color ?>';
	var x_axis_color = '<?cs var:repository_activity.chart_info.x_axis_color ?>';
	var y_axis_color = '<?cs var:repository_activity.chart_info.y_axis_color ?>';
	var x_grid_color = '<?cs var:repository_activity.chart_info.x_grid_color ?>';
	var y_grid_color = '<?cs var:repository_activity.chart_info.y_grid_color ?>';
	var tool_tip = '<?cs var:repository_activity.chart_info.tool_tip?>';
	var x_legend = '<?cs var:repository_activity.chart_info.x_legend?>';
	var y_legend = '<?cs var:repository_activity.chart_info.y_legend?>';

	var colorsArray = new Array();
	var index = 0;
	<?cs each:color = repository_activity.chart_info.colors ?>
		colorsArray[index] = '<?cs var:color ?>';
		index++;
	<?cs /each ?>

	try {
		var o = new OFC('<?cs var:repository_activity.chart_info.name ?>');
	} catch (error) {
		setTimeout("loadRepoActivityChart()",100);
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
	<?cs each:label = repository_activity.chart_info.x_labels ?>
		xArray[numLabelValues] = '<?cs var:label ?>';
		numLabelValues++;
	<?cs /each ?>
	o.xlabels = xArray;
	

	var maxY = 0;
	var numArrays = 0;
	var data_array = new Array(); 
	var keys_array = new Array(); 
	<?cs each:array = repository_activity.chart_info.data ?>
		keys_array[numArrays] = '<?cs var:array.author ?>';
		data_array[numArrays] = new Array();
		var data_number = 0;
		<?cs each:data_array = array.info ?>
			data_array[numArrays][data_number] = <?cs var:data_array ?>;
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
		if ( chart_type == 'Line' ){
			myData[ii] = new Line();
		}else {
			myData[ii] = new Bar();	
		}	
		myData[ii].values = data_array[ii];
		myData[ii].setKey(keys_array[ii],10);

		//myData[ii].changeColors(["#000000"]);	
		myData[ii].changeColors([colorsArray[ii%colorsArray.length]]);	
		o.addData(myData[ii]);
	}
        o.redraw();
     }
</script>


<!-- For displaying ticket activity chart -->
<script type="text/javascript">
//Pie chart
function loadTicketActivityChart(){
	//We pick up the data from the HDF
		
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
	var line_color = '<?cs var:ticket_activity.chart_info.line_color ?>';

	var colorsArray = new Array();
	var index = 0;
	<?cs each:color = repository_activity.chart_info.colors ?>
		colorsArray[index] = '<?cs var:color ?>';
		index++;
	<?cs /each ?>
	try {
		var oo = new OFC('<?cs var:ticket_activity.chart_info.name ?>');
	} catch (error) {
		setTimeout("loadTicketActivityChart()",100);
		return;
	}	

	oo.emptyDataList();
	oo.setTitle(chart_title);
	oo.set('bg_colour', bg_color);

	oo.xlabels = null;
	//Labels for x values
	var xArray = new Array();
	var numLabelValues = 0;
	<?cs each:label = ticket_activity.chart_info.x_labels ?>
		xArray[numLabelValues] = '<?cs var:label ?>';
		numLabelValues++;
	<?cs /each ?>
	oo.xlabels = xArray;
	
	var data_array = new Array(); 
	var data_index = 0;
	<?cs each:value = ticket_activity.chart_info.data ?>
		data_array[data_index] = <?cs var:value ?>
		data_index++;
	<?cs /each ?>
	var myData = new Pie();
	myData.values = data_array;
	myData.changeColors(colorsArray);
	myData.setAlpha(80);
	myData.setLineColor(line_color);
	oo.addData(myData);

	oo.redraw();	
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
	<?cs each:color = repository_activity.chart_info.colors ?>
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
		keys_array[numArrays] = '<?cs var:array.author ?>';
		data_array[numArrays] = new Array();
		var data_number = 0;
		<?cs each:data_array = array.info ?>
			data_array[numArrays][data_number] = <?cs var:data_array ?>;
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

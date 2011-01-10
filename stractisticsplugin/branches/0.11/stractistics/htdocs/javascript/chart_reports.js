
function array_max(_max, ar) {
	var max = _max;
	for (var i = 0; i < ar.length; i++) if (ar[i] > max) max = ar[i];
	return max;
}

function html_entity_decode(str) {
  var ta=document.createElement("textarea");
  ta.innerHTML=str.replace(/</g,"&lt;").replace(/>/g,"&gt;");
  return ta.value;
}

//-------------------------------------
//-------------------------------------
//In order to fully understand this function, take a look at the HDF.
function loadActivityChart(chart_info) {

	//We pick up the data from the HDF
		
	var y_numSteps = chart_info.y_steps;
	var x_orientation = chart_info.x_orientation;
	var x_font_size = chart_info.x_font_size;
	var chart_width = chart_info.width;
	var chart_height = chart_info.height;
	var num_results = chart_info.data_size;
	var x_font_color = chart_info.x_font_color;
	var chart_type = chart_info.type;
	var chart_title = chart_info.title;
	var bg_color = chart_info.bg_color;
	var x_axis_color = chart_info.x_axis_color;
	var y_axis_color = chart_info.y_axis_color;
	var x_grid_color = chart_info.x_grid_color;
	var y_grid_color = chart_info.y_grid_color;
	var tool_tip = html_entity_decode(chart_info.tool_tip);
	var x_legend = chart_info.x_legend;
	var y_legend = chart_info.y_legend;
	var colorsArray = chart_info.colors;

	try {
		var o = new OFC(chart_info.name);
	} catch (error) {
		setTimeout(loadActivityChart,100, chart_info);
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
	o.xlabels = chart_info.x_labels;	

	var maxY = 0;
	for (var i=0; i < chart_info.data.length; i++) {
		var data_set = {};
		var ar = chart_info.data[i];
		maxY = array_max(maxY, ar.info);

		if ( chart_type == 'Line' ) {
			data_set = new Line();
		} else {
			data_set = new Bar();	
		}
		data_set.values = ar.info;
		data_set.setKey(ar.author, 10);

		data_set.changeColors([colorsArray[i%colorsArray.length]]);	
		o.addData(data_set);
	}

	o.set('y_max',Math.ceil(maxY/y_numSteps)*y_numSteps);
	o.setTitle(chart_title);
        o.redraw();
}


// For displaying ticket activity chart 
//Pie chart
function loadActivityPieChart(chart_info) {
	//We pick up the data from the HDF
		
	var y_numSteps = chart_info.y_steps;
	var x_orientation = chart_info.x_orientation;
	var x_font_size = chart_info.x_font_size;
	var chart_width = chart_info.width;
	var chart_height = chart_info.height;
	var num_results = chart_info.data_size;
	var x_font_color = chart_info.x_font_color;
	var chart_type = chart_info.type;
	var chart_title = chart_info.title;
	var bg_color = chart_info.bg_color;
	var line_color = chart_info.line_color;

	var colorsArray = chart_info.colors;
	try {
		var oo = new OFC(chart_info.name);
	} catch (error) {
		setTimeout(loadActivityPieChart,100, chart_info);
		return;
	}	

	oo.emptyDataList();
	oo.setTitle(chart_title);
	oo.set('bg_colour', bg_color);
	oo.xlabels = chart_info.x_labels;
	
	var myData = new Pie();
	myData.values = chart_info.data;
	myData.changeColors(chart_info.colors);
	myData.setAlpha(80);
	myData.setLineColor(line_color);
	oo.addData(myData);

	oo.redraw();	
}


// For displaying Ticket activity chart
function loadUserActivityChart(chart_info){

	var y_numSteps = chart_info.y_steps;
	var x_orientation = chart_info.x_orientation;
	var x_font_size = chart_info.x_font_size;
	var chart_width = chart_info.width;
	var chart_height = chart_info.height;
	var num_results = chart_info.data_size;
	var x_font_color = chart_info.x_font_color;
	var chart_type = chart_info.type;
	var chart_title = chart_info.title;
	var bg_color = chart_info.bg_color;
	var x_axis_color = chart_info.x_axis_color;
	var y_axis_color = chart_info.y_axis_color;
	var x_grid_color = chart_info.x_grid_color;
	var y_grid_color = chart_info.y_grid_color;
	var tool_tip = html_entity_decode(chart_info.tool_tip);
	var x_legend = chart_info.x_legend;
	var y_legend = chart_info.y_legend;
	var colorsArray = chart_info.colors;
	try {
		var o = new OFC(chart_info.name);
	} catch (error) {
		setTimeout(loadUserActivityChart,100, chart_info);
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
	o.xlabels = chart_info.x_labels;

	var maxY = 0;
	var ii=0;
	for (var name in chart_info.data){
		var data_set = {};
		var data_points = chart_info.data[name];
		maxY = array_max(maxY, data_points);
		if ( chart_type == 'Line' ) {
			data_set = new Line();
		} else {
			data_set = new Bar();	
		}
		data_set.values = data_points;
		data_set.setKey(name, 10);
		data_set.changeColors([colorsArray[ii++%colorsArray.length]]);
		o.addData(data_set);
	}

	o.set('y_max',Math.ceil(maxY/y_numSteps)*y_numSteps);
	o.setTitle(chart_title);
        o.redraw();
}


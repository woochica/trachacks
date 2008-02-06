var OFC = Class.create({
	
	/*public static*/ supported: [
		/* bar charts */
		'bar', 'bar_3d', 'bar_fade', 'filled_bar', 'bar_glass',
		/* line charts */
		'line', 'line_dot', 'line_hollow',
		/* area charts */
		'area_hollow',
		/* pie charts */
		'pie'],
	
	/**
	 * @constructor
	 * @param {String} id ID of object/embed-element
	 * @return void
	 */
	initialize: function(id) {
		/* everytime set is called, redraw chart? */
		this.autoRedraw = false;
		
		/* SWF! */
		this.object = this.findSWF(id);
		
		// load x-labels as they are the only permanent stored object
		this.xlabels = [];
		this.xlabels = this.get('x_labels');
		
		// load data-objects
		this.dataList = [];
		this.getDataObjects();
	},
	
	debug: function() {
		var liste = this.getAll();
		var m = "";
		liste.each(function(pair) {
			m += pair.key + " - " + pair.value + "\n";
		}, this);
		alert (m);
	},
	
	/*################################################################\
	 * Flash communication methods
	\*###############################################################*/
	
	/**
	 * loads all the Dataobjects
	 * 
	 * @return Array
	 */
	/*public Array[OFCData]*/ getDataObjects: function() {
		var lvs = this.getAll();
		var datas = [];
		lvs.each(function(pair) {
			var ofcdataobj = null;
			var info = pair.key.split('_');
			var number = 0;
			if (info[info.length-1] == info[info.length-1] * 1) {
				number = info[info.length-1] * 1;
			}
			if (number > 0) {
				info.pop();
			}
			if (this.supported.indexOf(info.join('_')) == -1) {
				return;
			}
			switch (info[0]) {
				case 'filled':
				case 'bar':
					if (info.length > 1) {
						// solve inconsistency
						if (info[0] == 'filled') {
							ofcdataobj = new Bar('filled');
						} else {
							ofcdataobj = new Bar(info[1]);
						}
					} else {
						ofcdataobj = new Bar();
					}
				break;
				
				case 'pie':
					ofcdataobj = new Pie();
				break;
				
				case 'area':
					ofcdataobj = new Area('hollow');
				break;
				
				case 'line':
					if (info.length > 1) {
						ofcdataobj = new Line(info[1]);
					} else {
						ofcdataobj = new Line();
					}
				break;
			}
			
			ofcdataobj.number = number;
			var val = 'values';
			if (number > 0) {
				val += '_' + number;
			}
			ofcdataobj.values = this.get(val);
			ofcdataobj.fromData(this.deFlash(pair.value));
			
			this.dataList.push(ofcdataobj);
		}, this);
	},
	
	/**
	 * Adds a specified OFCData-object to the object list
	 * 
	 * @param {OFCData} data
	 */
	addData: function(/*OFCData*/ data) {
		data.number = this.dataList.length + (this.dataList.length > 0 ? 1 : 0);
		this.dataList[this.dataList.length] = data;
		data.addToOFC(this);
	},
	
	/**
	 * Replaces a specified old OFCData-object in the object list with the new
	 * one. Use getData to fetch the old one.
	 * 
	 * @param {OFCData} oldData
	 * @param {OFCData} newData
	 */
	replaceData: function(/*OFCData*/ oldData, /*OFCData*/ newData) {
		// find position in dataList
		var pos = 0;
		for (; pos < this.dataList.length; pos++) {
			if (this.dataList[pos].number = oldData.number) break;
		}
		pos--;
		
		// copy number
		newData.number = oldData.number;
		
		// delete old one
		delete this.dataList[pos];
		oldData.removeFromOFC(this);
		delete oldData;
		
		// save new one
		this.dataList[pos] = newData;
	},
	
	/**
	 * removes a specified OFCData-object from the object list
	 * 
	 * @param {OFCData} position
	 */
	removeData: function(/*OFCData*/ data) {
		var pos = 0;
		for (; pos < this.dataList.length; pos++) {
			if (this.dataList[pos].number = data.number) break;
		}
		
		this.dataList[pos].removeFromOFC(this);
		this.dataList = $A(this.dataList).without(this.dataList[pos]);
		this.reOrder();
	},
	
	/**
	 * returns the specified OFCData-object
	 * if the object is not found null is returned
	 * 
	 * @param {int} number Number of the data-set in ofc (0, 2, 3, 4...)
	 * @type {OFCData}
	 */
	getData: function(number) {
		for (var i = 0; i < this.dataList.length; i++) {
			if (this.dataList[i].number == number) return this.dataList[i];
		}
		return null;
	},
	
	/**
	 * resets the datalist - removes all OFCData-objects
	 * @param {Array} exceptions
	 */
	emptyDataList: function(exceptions) {
		for (var i = 0; i < this.dataList.length; i++) {
			if (typeof exceptions != 'undefined') {
				var cont = false;
				$A(exceptions).each(function(data) {
					if (this.dataList[i].equals(data)) {
						cont = true;
						throw $break;
					}
				}, this);
				if (cont) continue;
			}
			this.dataList[i].removeFromOFC(this);
			this.dataList = $A(this.dataList).without(this.dataList[i]);
		}
		this.reOrder();
	},
	
	/**
	 * returns an empty OFCData-object based on the defined name
	 * if the name is not supported null is returned
	 * 
	 * @param {String} type
	 * @type {OFCData}
	 */
	getDataFromType: function(type) {
		if (this.supported.indexOf(type) == -1) return null;
		
		switch (type) {
			case 'bar':
				return new Bar();
				break;
			
			case 'bar_filled':
			case 'filled_bar':
				return new Bar('filled');
				break;
			
			case 'bar_fade':
				return new Bar('fade');
				break;
			
			case 'bar_glass':
				return new Bar('glass');
				break;
			
			case 'bar_3d':
				return new Bar('3d');
				break;
			
			case 'line':
				return new Line();
				break;
			
			case 'line_hollow':
				return new Line('hollow');
				break;
			
			case 'line_dot':
				return new Line('dot');
				break;
			
			case 'area_hollow':
				return new Area('hollow');
				break;
			
			case 'pie':
				return new Pie();
				break;
		}
	},
	
	/**
	 * Reorders the OFCData-objects (gives them new numbers)
	 */
	reOrder: function() {
		for (var i = 0; i < this.dataList.length; i++) {
			// fill gap in list!
			var n = i + (i > 0 ? 1 : 0);
			
			this.dataList[i].number = n;
			this.dataList[i].addToOFC(this);
		}
	},
	
	/**
	 * Returns all LoadVars-parameters set in the flashobject
	 * 
	 * @return {Hash}
	 */
	getAll: function() {
		var vars = this.object.getAllLVVars().split('&');
		var lvs = new Hash();
		// walk through LoadVars in reverse order
		// no one knows why flash sends them in this order *rolleyes*
		// however order is important!
		for (var i = vars.length - 1; i >= 0; i--) {
			var val = vars[i].split('=');
			if (unescape(val[0]).blank()) continue;
			lvs.set(unescape(val[0]), unescape(val[1]));
		}
		return lvs;
	},
	
	/**
	 * Sets a specified parameter of the LoadVars to the given data.
	 * Data can be String, int or Array. If its an Array it gets converted
	 * to a comma-separated string automatically
	 * 
	 * @param {String} name name of parameter
	 * @param {mixed} value value of parameter
	 * @return void
	 */
	set:function(name,value) {
		if (value != null && typeof value == 'object') value = this.makeFlashing(value);
		this.object.setLVVar(name,value);
		if (this.autoRedraw) {
			this.redraw();
		}
	},
	
	/**
	 * Returns the value of a specified LoadVar-parameter.
	 * Per default this function always returns an array. If the value is
	 * a comma-separated string it is splited. If you don't want this
	 * behaviour, set deFlash to false
	 * 
	 * @param {String} name name of parameter
	 * [@param {bool} deFlash if set to true, it always returns]
	 * @return {mixed}
	 */
	get:function(name, deFlash) {
		if (typeof deFlash == 'undefined') deFlash = true;
		var str = this.object.getLVVar(name);
		if (typeof str == 'undefined' || str == 'undefined') {
			if (deFlash) return [];
			return '';
		}
		if (deFlash) {
			return this.deFlash(str);
		}
		return str;
	},
	
	/**
	 * Redraws the flash-object. This function should be called after all
	 * changes have been applied.
	 * 
	 * @return void;
	 */
	redraw:function() {
		// take labels
		this.set('x_labels', this.xlabels);
		
		// reset all objects
		this.reOrder();
		
		// redraw
		this.object.redraw();
	},
	
	/**
	 * Finds the SWF-object. This is browserdependent
	 * 
	 * @access private			this.dataList[i].addToOFC(this);
	 
	 * @param {String} movieName name assigned to object or embed
	 * @return {Element}
	 */
	findSWF: function(movieName) {
		if (navigator.appName.indexOf('Microsoft')!= -1) {
			return window[movieName];
		} else {
			return document[movieName];
		}
	},
	
	/**
	 * Joins the given array using , (comma) and returns it
	 * 
	 * @param {Array} arr
	 * @return {String}
	 */
	makeFlashing: function(arr) {
		return arr.join(',');
	},
	
	/**
	 * Exlpodes the given string using , (comma) and returns it
	 * 
	 * @param {String} str
	 * @return {Array}
	 */
	deFlash: function(str) {
		var arr = str.split(',');
		if (arr.length == 1 && arr[0] == '') return [];
		return arr;
	},
	
	/*################################################################\
	 * Wrapper methods
	\*###############################################################*/
	
	/**
	 * Defines the charts title
	 * 
	 * @param {String} text Title's text
	 * @param {String} css Title's format
	 */
	/*public void*/ setTitle: function(text, css) {
		if (typeof css == 'undefined' || css == null) {
			var title = this.get('title');
			if (title.length == 2) css = title[1];
			else css = '{font-size:20px,color:#000000}';
		}
		this.set('title', [
			text
		,	css
		]);
	},
	
	/**
	 * Defines the charts legend
	 * Unlike the PHP-Library there is only one setLegend-Method - use the first
	 * parameter to define which legend should be set
	 * 
	 * @param {String} type can be y, x or y2
	 * @param {String} text Legends value
	 * @param {int} size Legends size
	 * @param {String} color Legends color
	 */
	/*public void*/ setLegend: function(type, text, size, color) {
		type += '_legend'
		var legend = this.get(type);
		if (typeof text == 'undefined' || text == null) {
			if (legend.length > 0) text = legend[0];
			else text = null;
		}
		if (typeof size == 'undefined' || size == null) {
			if (legend.length > 1) size = legend[1];
			else size = 10;
		}
		if (typeof color == 'undefined' || color == null) {
			if (legend.length > 2) color = legend[2];
			else color = '#000000';
		}
		this.set(type, [
			text
		,	size
		,	color
		]);
	},
	
	/**
	 * Applies a given color-scheme to the chart. The first four params are
	 * easy to understand. The last one is an Array of colors, which is used
	 * for the different data-sets
	 * 
	 * @param {String} bgcolor Background color
	 * @param {String} textcolor Text color
	 * @param {String} axiscolor Axis color
	 * @param {String} gridcolor Grid color
	 * @param {Array} datacolors List of colors used to color the bars/lines...
	 * @return void
	 */
	/*public void*/ setColorScheme: function(bgcolor,textcolor,axiscolor,gridcolor,datacolors) {
		if (typeof datacolors != 'object') return;
		
		// background
		this.set('bg_colour', bgcolor);
		
		// axis
		this.setAxisColor(gridcolor);
		
		// grid
		this.setGridColor(gridcolor);
		
		// title
		var title = this.get('title');
		if (title.length > 0) {
			var css = '';
			if (title.length > 1) {
				css = title[1];
				var replacer = /color:(#[a-zA-Z0-9]{6})/g
				css = css.replace(replacer, 'color:'+textcolor);
			}
			this.setTitle(title[0], css);
		}
		
		// legends
		this.setLegend('x', null, null, textcolor);
		this.setLegend('y', null, null, textcolor);
		this.setLegend('y2', null, null, textcolor);
		
		// labels
		var ylabel = this.get('y_label_style');
		if (ylabel.length > 0) {
			size = ylabel[0];
		} else {
			size = 10;
		}
		this.setYLabelStyle(size, textcolor);
		
		var y2label = this.get('y2_label_style');
		if (y2label.length > 0)
		this.setRightYLabelStyle(y2label[0], textcolor);
		
		var xlabel = this.get('x_label_style');
		if (xlabel.length > 0)
		this.setXLabelStyle(xlabel[0], textcolor, xlabel[2], xlabel[3], xlabel[4]);
		
		var j = 0;
		for (var i = 0; i < this.dataList.length; i++) {
			// special treatment for pie
			if (this.dataList[i].mainType == 'pie') {
				this.dataList[i].changeColors(datacolors);
				break;
			}
			this.dataList[i].changeColors([datacolors[j]]);
			j++;
		}
	},
	
	/**
	 * Converts the the first given OFCData-object to the second (blank)
	 * OFCData-Object and returns the new one. Typical usage would be:
	 * 
	 * var old = ofc.getData(0); // get first data-set
	 * var filled = ofc.convert(old, new Bar('filled'));
	 * ofc.redraw();
	 * 
	 * @param {OFCData} oldData
	 * @param {OFCData} newData
	 * @type {OFCData}
	 * @return Returns the converted object
	 */
	convert: function(/*OFCData*/ oldData, /*OFCData*/ newData) {
		// do the f**** transformation
		newData.convertFrom(oldData);
		
		// replace them!
		this.replaceData(oldData, newData);
		
		return newData;
	},
	
	/**
	 * Does the same as convert, but automatically with all OFCData-objects
	 * 
	 * @param {OFCData} newData The new data type
	 */
	convertAll: function(/*OFCData*/ newData) {
		for (i = 0; i < this.dataList.length; i++) {
			var newDataClone = Object.clone(newData);
			this.convert(this.dataList[i], newData);
		}
		// belive it or not, but thats it.
	},
	
	/**
	 * Defines the y label style
	 * 
	 * @param {int} size Font size
	 * @param {String} color Font color
	 */
	/*public void*/ setYLabelStyle: function(size,color) {
		this.set('y_label_style', [
			size
		,	color
		]);
	},
	
	/**
	 * Defines the right y label style
	 * 
	 * @param {int} size Font size
	 * @param {String} color Font color
	 */
	/*public void*/ setRightYLabelStyle: function(size,color) {
		this.set('y2_label_style', [
			size
		,	color
		]);
	},
	
	/**
	 * Defines the x label style
	 * orientation defaults to 0
	 * step defaults to -1
	 * grid defaults to the label-color
	 * 
	 * @param {int} size Font size
	 * @param {String} color Font color
	 * [@param {int} orientation 0 = horizontal, 1 = vertical, 2 = 45 degrees]
	 * [@param {int} step every step a colored line is drawn in the grid]
	 * [@param {String} grid Grid color at step postion
	 */
	/*public void*/ setXLabelStyle: function(size,color,orientation,step,grid) {
		if (typeof grid == 'undefined') grid = color;
		if (typeof step == 'undefined') step = -1;
		if (typeof orientation == 'undefined') orientation = 0;
		this.set('x_label_style', [
				size
			,	color
			,	orientation
			,	step
			,	grid]);
	},
	
	/**
	 * Sets the y and x grid color at the same time
	 * 
	 * @param {String} color
	 */
	/*public void*/ setGridColor: function(color) {
		this.set('x_grid_colour', color);
		this.set('y_grid_colour', color);
	},
	
	/**
	 * Sets the y and x axis color at the same time
	 * 
	 * @param {String} color
	 */
	/*public void*/ setAxisColor: function(color) {
		this.set('x_axis_colour', color);
		this.set('y_axis_colour', color);
	},
	
	/**
	 * Sets the labels for the chart
	 * 
	 * @param {Array} labels Array of Strings
	 */
	/*public void*/ setXLabels: function(labels) {
		this.xlabels = labels;
	}
});
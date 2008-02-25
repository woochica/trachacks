/**
 * Pie-Class
 * 
 */
var Pie = Class.create(OFCData, {
	/* supported subtypes */
	/*public static*/ supported: [
		null
	],
	
	/**
	 * @constructor
	 * @class Pie
	 * @extends OFCData
	 * @param {String} sub subtype
	 */
	initialize: function($super, sub) {
		if (typeof sub == 'undefined') sub = null;
		$super('pie', sub);
		
		// pie style specific properties
		// alpha-value
		this.alpha = null;
		// pie line color
		this.lineColor = null;
		// color of labels
		this.labelColor = null;
		// gradient
		this.gradient = null;
		// border size
		this.borderSize = null;
		// colors of elements
		this.colors = [];
		// links
		this.links = [];
	},
	
	/**
	 * Converts another OFCData-object to this one
	 * 
	 * @param {OFCData} chart Object to copy from
	 */
	convertFrom: function(/* OFCData */ chart) {
		var colors = chart.getColors();
		if (colors.length > 0) {
			this.lineColor = colors[0];
		}
		if (colors.length > 1) {
			this.labelColor = colors[1];
		}
		if (colors.length > 2) {
			for (var i = 2; i < colors.length; i++) {
				this.colors.push(colors[i]);
			}
		}
		this.setKey(chart.key, chart.keySize);
		
		this.values = chart.values;
	},
	
	
	/**
	 * @see OFCData#toData
	 */
	toData: function() {
		var values = [];
		if (this.alpha != null) values[0] = this.alpha;
		if (typeof values[0] == 'undefined') values[0] = 60;
		if (this.lineColor != null) values[1] = this.lineColor;
		if (typeof values[1] == 'undefined') values[1] = '#99CCFF';
		if (this.labelColor != null) values[2] = this.labelColor;
		if (typeof values[2] == 'undefined') values[2] = '#000000';
		var c = 0;
		if (this.gradient != null) {
			if (this.gradient != null) values[2] = this.gradient;
			if (typeof values[3] == 'undefined') values[3] = 0;
			c = 1;
		}
		if (this.borderSize != null) values[3+c] = this.borderSize;
		if (typeof values[3+c] == 'undefined') values[3+c] = 1;
		
		return values;
	},
	
	/**
	 * @see OFCData#fromData
	 */
	fromData: function(info) {
		this.alpha = info[0];
		this.labelColor = info[1];
		this.lineColor = info[2];
		c = 0;
		if (info.length > 4) {
			this.gradient = info[3];
			c = 1;
		}
		if (info.length > 3) {
			this.borderSize = info[4+c];
		}
	},
	
	/**
	 * @see OFCData#getColors
	 */
	getColors: function() {
		return [this.lineColor, this.labelColor];
	},

	/**
	 * @see OFCData#getColors
	 */
	changeColors: function(colors) {
		this.lineColor = colors[0];
		if (colors.length > 1) {
			this.labelColor = colors[1];
		}
		if (colors.length > 2) {
			for (var i = 2; i < colors.length; i++) {
				this.colors.push(colors[i]);
			}
		}
	},
	
	setLineColor: function(color){
		this.lineColor = color;
	},
	
	setLabelColor: function(color){
		this.labelColor = color;
	},
	
	setAlpha: function(alpha){
		this.alpha = alpha;
	},

	/**
	 * @see OFCData#getFullName
	 */
	getFullName: function() {
		
		var name = 'pie';
		
		if (this.subType != null) {
			name += '_'+this.subType;
		}
		
		if (this.number != 0) {
			name += '_'+this.number;
		}
		
		return name;
	},
	
	/**
	 * @see OFCData#addToOFC
	 */
	addToOFC: function($super, /*OFC*/ ofc) {
		// we have to kill all other data-elements, before calling super
		// if we are not the only one
		if (ofc.dataList.length > 1) {
			ofc.emptyDataList([this]); // all except this
		}
		$super(ofc);
		
		// convert labels
		ofc.set('pie_labels', ofc.get('x_labels'));
		ofc.set('x_labels', null);
		
		if (this.colors.length == 0) {
			this.colors = [this.lineColor];
		}
		ofc.set('colours', this.colors);
		
		if (this.links.length > 0) {
			ofc.set('pie_links', this.links);
		}
	},

	
	/**
	 * @see OFCData#addToOFC
	 */
	removeFromOFC: function($super, /*OFC*/ ofc) {
		$super(ofc);
		ofc.set('x_labels', ofc.get('pie_labels'));
		ofc.set('pie_labels', null);
		ofc.set('colours', null);
		ofc.set('pie_links', null);
	}
});
/**
 * Bar-Class
 * 
 */
var Bar = Class.create(OFCData, {
	/* supported subtypes */
	/*public static*/ supported: [
		null,
		'filled',
		'fade',
		'glass',
		'3d'
	],
	
	/**
	 * @constructor
	 * @class Bar
	 * @extends OFCData
	 * @param {String} sub subtype
	 */
	initialize: function($super, sub) {
		if (typeof sub == 'undefined') sub = null;
		$super('bar', sub);
		
		// bar style specific properties
		// alpha-value
		this.alpha = null;
		// inner bar color
		this.innerColor = null;
		// border-color or second color for filled and glass-bar
		this.outerColor = null;
		// 3d-x-axis-size
		this.xAxis3D = 15;
	},
	
	/**
	 * Converts another OFCData-object to this one
	 * 
	 * @param {OFCData} chart Object to copy from
	 */
	convertFrom: function(/* OFCData */ chart) {
		var colors = chart.getColors();
		if (colors.length > 0) {
			this.innerColor = colors[0];
		}
		if (colors.length > 1) {
			this.outerColor = colors[1];
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
		if (this.innerColor != null) values[1] = this.innerColor;
		if (typeof values[1] == 'undefined') values[1] = '#99CCFF';
		var c = 0;
		switch (this.subType) {
			case 'filled':
			case 'glass':
				if (this.outlineColor != null) values[2] = this.outlineColor;
				if (typeof values[2] == 'undefined') values[2] = '#88BBEE';
				c = 1;
			break;
		}
		if (this.key != null) values[2+c] = this.key;
		if (typeof values[2+c] == 'undefined') values[2+c] = 'Unnamed Bar';
		if (this.keySize != null) values[3+c] = this.keySize;
		if (typeof values[3+c] == 'undefined') values[3+c] = 10;
		
		return values;
	},
	
	/**
	 * @see OFCData#fromData
	 */
	fromData: function(info) {
		this.alpha = info[0];
		if (info.length > 1) {
			this.innerColor = info[1];
		}
		c = 0;
		if (this.subType == 'filled' || this.subType == 'glass' && info.length > 4) {
			this.innerColor = info[2];
			c = 1;
		}
		this.setKey(info[2+c], info[3+c]);
	},
	
	/**
	 * @see OFCData#getColors
	 */
	getColors: function() {
		return [this.innerColor, this.outerColor];
	},

	/**
	 * @see OFCData#getColors
	 */
	changeColors: function(colors) {
		this.innerColor = colors[0];
		if (colors.length > 1) {
			this.outerColor = colors[1];
		}
	},

	/**
	 * @see OFCData#getFullName
	 */
	getFullName: function() {
		
		var name = 'bar';
		
		if (this.subType == 'filled') {
			// solve inconsistency
			name = 'filled_bar';
		} else if (this.subType != null) {
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
		$super(ofc);
		
		if (this.subType == '3d') {
			ofc.set('x_axis_3d', this.xAxis3D);
		}
	},

	
	/**
	 * @see OFCData#addToOFC
	 */
	removeFromOFC: function($super, /*OFC*/ ofc) {
		$super(ofc);
		
		if (this.subType == '3d') {
			ofc.set('x_axis_3d', null);
		}
	}
});
/**
 * Line-Class
 */
var Line = Class.create(OFCData, {
	/* supported subtypes */
	/*public*/ supported: [
		null,
		'dot',
		'hollow'
	],
	
	/**
	 * @constructor
	 * @class Line
	 * @extends OFCData
	 * @param {String} sub subtype
	 */
	initialize: function($super, sub) {
		if (typeof sub == 'undefined') sub = null;
		$super('line', sub);
		
		/**
		 * line style specific
		 */
		/* line-width */
		this.width = null;
		
		/* line color */
		this.color = null;
		
		/* circle size for hollow and dot lines */
		this.dotSize = null;
		
	},
	
	
	/**
	 * Converts another OFCData-object to this one
	 * 
	 * @param {OFCData} chart Object to copy from
	 */
	convertFrom: function(/* OFCData */ chart) {
		var colors = chart.getColors();
		if (colors.length > 0) {
			this.color = colors[0];
		}
		this.setKey(chart.key, chart.keySize);
		
		this.values = chart.values;
	},
	
	
	/**
	 * @see OFCData#toData
	 */
	toData: function() {
		var values = [];
		
		if (this.width != null) values[0] = this.width;
		if (typeof values[0] == 'undefined') values[0] = 2;
		if (this.color != null) values[1] = this.color;
		if (typeof values[1] == 'undefined') values[1] = '#99CCFF';
		if (this.key != null) values[2] = this.key;
		if (typeof values[2] == 'undefined') values[2] = 'Unnamed Line';
		if (this.keySize != null) values[3] = this.keySize;
		if (typeof values[3] == 'undefined') values[3] = 10;
		
		switch (this.subType) {
			case 'hollow':
			case 'dot':
				if (this.dotSize != null) values[4] = this.dotSize;
				if (typeof values[4] == 'undefined') values[4] = values[0] + 3;
			break;
		}
		
		return values;
	},
	
	/**
	 * @see OFCData#fromData
	 */
	fromData: function(info) {
		this.width = info[0];
		this.color = info[1];
		this.setKey(info[2], info[3]);
		if (info.length > 4) {
			this.dotSize = info[4];
		}
	},
	
	/**
	 * @see OFCData#getColors
	 */
	getColors: function() {
		return [this.color];
	},

	/**
	 * @see OFCData#getColors
	 */
	changeColors: function(colors) {
		this.color = colors[0];
	},

	/**
	 * @see OFCData#getFullName
	 */
	getFullName: function() {
		
		var name = 'line';
		
		if (this.subType != null) {
			name += '_'+this.subType;
		}
		
		if (this.number != 0) {
			name += '_'+this.number;
		}
		
		return name;
	}
});
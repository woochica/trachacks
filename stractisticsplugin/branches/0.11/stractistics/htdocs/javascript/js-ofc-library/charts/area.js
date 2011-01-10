/**
 * Area-Class
 */
var Area = Class.create(OFCData, {
	/* supported subtypes */
	/*public*/ supported: [
		'hollow'
	],
	
	/**
	 * @constructor
	 * @class Area
	 * @extends OFCData
	 * @param {String} sub subtype
	 */
	initialize: function($super, sub) {
		if (typeof sub == 'undefined') sub = 'hollow';
		$super('area', sub);
		
		/**
		 * area style specific
		 */
		/* line-width */
		this.width = null;
		
		/* alpha of area */
		this.alpha = 70;
		
		/* line color */
		this.color = null;
		
		/* area color */
		this.fillColor = null;
		
		/* circle size */
		this.dotSize = 3;
		
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
			this.fillColor = colors[0];
		}
		if (colors.length > 1) {
			this.fillColor = colors[1];
		}
		this.setKey(chart.ke, chart.keySize);
		
		this.values = chart.values;
	},
	
	
	/**
	 * @see OFCData#toData
	 */
	toData: function() {
		var values = [];
		
		if (this.width != null) values[0] = this.width;
		if (typeof values[0] == 'undefined') values[0] = 2;
		
		if (this.dotSize != null) values[1] = this.dotSize;
		
		if (this.color != null) values[2] = this.color;
		if (typeof values[2] == 'undefined') values[2] = '#99CCFF';
		
		values[3] = this.alpha;
		
		if (this.key != null) values[4] = this.key;
		if (typeof values[4] == 'undefined') values[4] = 'Unnamed Area';
		if (this.keySize != null) values[5] = this.keySize;
		if (typeof values[5] == 'undefined') values[5] = 10;
		
		if (this.fillColor != null) values[6] = this.fillColor;
		values[6] = this.fillColor;
		
		alert('setting info '+values.inspect());
		return values;
	},
	
	/**
	 * @see OFCData#fromData
	 */
	fromData: function(info) {
		alert('getting info '+info.inspect());
		this.width = info[0];
		this.dotSize = info[1];
		this.color = info[2];
		this.alpha = info[3]
		this.setKey(info[4], info[5]);
		if (info.length > 6) {
			this.fillColor = info[6];
		} else {
			this.fillColor = this.color;
		}
	},
	
	/**
	 * @see OFCData#getColors
	 */
	getColors: function() {
		return [this.color, this.fillColor];
	},

	/**
	 * @see OFCData#getColors
	 */
	changeColors: function(colors) {
		this.color = colors[0];
		if (colors.length > 1) {
			this.fillColor[1] = colors[1];
		}
	},

	/**
	 * @see OFCData#getFullName
	 */
	getFullName: function() {
		
		var name = 'area';
		
		if (this.subType != null) {
			name += '_'+this.subType;
		}
		
		if (this.number != 0) {
			name += '_'+this.number;
		}
		
		return name;
	}
});
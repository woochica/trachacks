/**
 * This is an abstract class representing one data line in the chart
 *
 * @version 0.1
 * @requires OFC, Prototype
 * @author Matthias Steinböck grillen at abendstille at
 */
/* abstract */ var OFCData = Class.create({

 /**
 * Initializes the Data-Object with a main-type and a sub-type.
 * e.g. if you want to create a bar-chart
 */
 initialize: function(main, sub) {

 // check if type supported
 if (this.supported.indexOf(sub) == -1) {
 alert('OFC-JS-ERROR: subtype '+sub.inspect()+' is not supported by '+main+'.');
 return null;
 }

 // create properties
 this.mainType = main;
 this.subType = sub;
 this.number = null;
 this.values = null;

 // key style TODO: make accepting CSS
 this.key = '';
 this.keySize = 10;
 },

 /**
 * Sets the key (the data-name) and its font-size
 * @access public
 * @param {String} text Dataname
 * @param {int} size Fontsize
 * @return void
 */
 setKey: function(text, size) {
 if (typeof size != 'undefined') {
 this.keySize = size;
 }
 this.key = text;
 },

 /**
 * saves this data to the given ofc-objcet
 * @access public
 * @param {OFC} ofc An instance of ofc
 * @param {int} number The datas number in the chart
 * @return void
 */
 addToOFC: function(/* OFC */ ofc) {

 // prepare param-names
 var value = 'values';

 if (this.number != null && this.number != 0) {
 value += '_'+this.number;
 }

 // set on ofc
 ofc.set(this.getFullName(), this.toData());

 // set value for this data
 ofc.set(value, this.values);
 },

 /**
 * removes the data from the ofc-object
 * @access public
 * @param {OFC} ofc An instance of ofc
 * @return void
 */
 removeFromOFC: function(/* OFC */ ofc) {
 // prepare param-names
 var value = 'values';

 if (this.number != 0) {
 value += '_'+this.number;
 }

 ofc.set(this.getFullName(), null);
 ofc.set(value, null);
 },

 /**
 * Method-stub - should be overwritten
 * Returns the full param name in ofc
 *
 * @return {String}
 */
 getFullName: function() {
 var name = this.mainType;

 if (this.subType != null) {
 name += '_'+subType;
 }

 if (this.number != 0) {
 name += '_'+number;
 }
 return name;
 },

 /**
 * Method-stub - should be overwritten
 * Returns the full value string in ofc
 *
 * @return {Aray}
 */
 toData: function() {
 return [];
 },

 /**
 * Method-stub - should be overwritten
 *
 * Loads all required data from the string
 * @param {Array} info
 */
 fromData: function(info) {
 return null;
 },

 /**
 * Method-stub - should be overwritten
 *
 * Returns all colors of the this OFCData
 * @return Array
 */
 getColors: function() {
 return [];
 },

 /**
 * Method-stub - should be overwritten
 *
 * Changes this objects colors
 * @param {Array} colors
 */
 changeColors: function(colors) {
 return null;
 },

 /**
 * Compares another OFCData-object to this for equality
 *
 * @param {OFCData} other
 * @type boolean
 */
 equals: function(/*OFCData*/ other) {
 return this.mainType == other.mainType
 && this.subType == other.subType
 && this.number == other.number;
 }
});
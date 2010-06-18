//
// Date additions
//
Date.prototype.getDaysInMonth = function(){
  var zeroBasedMonth = this.getMonth();
  //if your in months with 31 days
  if(zeroBasedMonth === 0 || zeroBasedMonth == 2 
	  || zeroBasedMonth == 4 || zeroBasedMonth == 6 
	  || zeroBasedMonth == 7 || zeroBasedMonth == 9 
	  || zeroBasedMonth == 11) 
	 return 31;
  else if (zeroBasedMonth == 3 || zeroBasedMonth == 5 || zeroBasedMonth == 8 
			  || zeroBasedMonth == 10 ) 
	 return 30;
  else if( this.getYear() %4 === 0 ) 
	 return 29;
  else 
	 return 28;
};
Date.prototype.getDaysInMonth.__doc__ = "Returns the Number of days in the current Month";

if(!Date.prototype.reconfigured){
  Date.prototype.oldGetYear = Date.prototype.getYear;
  Date.prototype.reconfigured = true;
  Date.prototype.getYear = function(){
    var x = Date.prototype.oldGetYear.call(this);
    if(x < 1000)
      return x+1900;
    else
      return x;
  };
}

Date.prototype.getMonthString = function(){
  return this.toDateString().split(' ')[1];
};

Date.prototype.toShortString = function(){
  var str = new String((this.getMonth()+1)).padLeft('0',2) +'/'+
  new String(this.getDate()).padLeft('0', 2) + "/"+
  this.getFullYear()+" "+
  this.getHours()+":"+
  new String( this.getMinutes() ).padLeft('0',2);
  return str;
};
Date.prototype.toShortString.__doc__ = 'function(): returns ##/##/#### ##:## format date string';

Date.prototype.toShortDateString = function(){
  var str = new String((this.getMonth()+1)).padLeft('0',2) +'/'+
  new String(this.getDate()).padLeft('0', 2) + "/"+
  this.getFullYear();
  return str;
};
Date.prototype.toShortDateString.__doc__ = 'function(): returns ##/##/#### format date string';

Date.prototype.toTimeString = function(){
  var str = new String(this.getHours())+":"+
  new String( this.getMinutes() ).padLeft('0',2) + ":" +
  new String( this.getSeconds() ).padLeft('0',2);
  return str;
};
Date.prototype.toTimeString.__doc__ = 'function(): returns ##:##:## format date string';



window.registerElements = function(obj){
  for(var i = 1; i < arguments.length; i++){
	 var elemId = arguments[i];
	 obj[elemId] = document.getElementById(elemId);
  }
};

window.stripNonNumeric = function(id){
  if(id){
	 var result = '';
	 for(var i = 0; i < id.length; i++){ 
		var c = id[i];
		if(! isNaN(parseInt(c))) 
		  result += c;
	 }
	 return result;
  }
};

(function(){
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  window.__query__ = {};
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    window.__query__[pair[0]] = pair[1];
  } 
})()

//
// Cross Platform Event Adding
//
function AddEventListener( elem, evt, func, capture){
  capture = capture || false;
  if(elem.addEventListener) elem.addEventListener( evt, func, capture);
  else elem.attachEvent('on'+evt, func);
  return func;
};
AddEventListener.__doc__ = 'This adds CrossPlatform event adding.  You want to use AddEventListenerWithTarget if you want to get the event and target : AddEventListener( elem, evt, func, capture)';

///
///Better Cross PLatform Event Adding
///
function AddEventListenerWithTarget( elem, evt, func, capture){
  var newFunc = function( event ){
	 var target;
	 if(!event) event = window.event;
	 if(event.target) target = event.target;
	 else if(event.srcElement) target = event.srcElement;
	 if(target.nodeType == 3) // Safari bug
		target = target.parentNode;
	 func( event, target );
  }
  AddEventListener(elem, evt, newFunc, capture || false);
  return newFunc;
}
AddEventListener.__doc__ = 'This adds CrossPlatform event adding with the event and target : RemoveEventListener(elem, evt, func, capture)';

//
// Cross Platform Event Removal
//
function RemoveEventListener(elem, evt, func, capture){
  capture = capture || false;
  if(elem.removeEventListener) elem.removeEventListener( evt, func, capture);
  else elem.detachEvent('on'+evt, func);
}
RemoveEventListener.__doc__ = "Removes event handlers in a cross platform way : RemoveEventListener(elem, evt, func, capture) ";

// Cross Platform Event Propagation stopping
function stopPropagation(event){
  if (window.event) { 
	 window.event.cancelBubble = true; 
	 window.event.returnValue = false;
  }
  if (event && event.preventDefault && event.stopPropagation) {
	 event.preventDefault();
	 event.stopPropagation();
  } 
  return false;
}
stopPropagation.__doc__ = "Cross Platform Event Propagation stopping;  IN IE you need to return false or the value of stopPropogation (which is false)";


function map(fn, list, thisObj){
  var len = list.length;
  var arr = new Array();
  for( var i = 0 ; i < len ; i++ )
	 arr.push( fn.call(thisObj, list[i] ) );

  return arr;
}
  

function mapFlatten(fn, list, thisObj){
  var len = list.length;
  var arr = new Array();
  for( var i = 0 ; i < len ; i++ )
	 arr = arr.concat( fn.call(thisObj, list[i] ) );

  return arr;
}

window.forEach = function ( fn, list, thisObj ) {
  if(list){
	 var len = list.length;
	 for( var i = 0 ; i < len ; i++ )
		fn.call(thisObj, list[i], i );
  }
};


window.filter = function (fn, list, thisObj){
  var arr = [];
  for( var i=0 ; i < list.length ; i++ )
	 if(fn.call(thisObj, list[i])) 
		arr.push(list[i]);
  return arr;
};


///
///Just here for cross library compatability.
/// Also, not a bad function Just takes the list of ids and returns the list of elements
///
if( typeof($$) == 'undefined'){
  function $$ () {
	 var elements = new Array();
	 
	 for (var i = 0; i < arguments.length; i++) {
		var element = arguments[i];
		if (typeof(element) == 'string')
		  element = document.getElementById(element);
		
		if (arguments.length == 1) 
		  return element;
		
		elements.push(element);
	 }
	 
	 return elements;
  }
 }
  
  String.prototype.removeLeadingRdf = function (){
	 var s = this.toLowerCase();
	 s = s.substring(0,4);
	 if(s == 'rdf:') s = this.substring(4,this.length)
	 else s = this;
	 return s;
  };
String.prototype.removeLeadingRdf.__doc__ = 'returns a new string minus the leading rdf: if it exists';

String.prototype.format = function (hash){
  var item, s = this;
  var regex;
  for( item in hash ){
	 regex = new RegExp('{'+item+'}', 'g');
	 s = s.replace(regex, hash[item]);
  }
  return s;
};
String.prototype.format.__doc__ = "function( hashtable ) : accepts a hashtable of name value pairs to replace in the string";

String.prototype.padLeft = function( str , len ){
  var oldstr = this;
  while(oldstr.length < len){ oldstr = str+oldstr; };
  return oldstr;
};
String.prototype.padLeft.__doc__ = 'function( str , len ) : pads this string with str until the string.length >= len';

String.prototype.padRight = function( str , len ){
  var oldstr = this;
  while(oldstr.length < len){ oldstr = oldstr+str; };
  return oldstr;
};
String.prototype.padRight.__doc__ = 'function( str , len ) : pads this string with str until the string.length >= len';

String.prototype.trim = function() {
  //Match spaces at beginning and end of text and replace
  //with null strings
  return this.replace(/^\s+/,'').replace(/\s+$/,'');
};
String.prototype.trim.__doc__ = 'trims leading and trailing space';



//
//Array additions
//

if( !Array.prototype.map ) 
  Array.prototype.map = function( fn, thisObj) {
	 return map( fn, this, thisObj );
  };

if(!Array.prototype.forEach) 
  Array.prototype.forEach = function (fn, thisObj) {
	 return window.forEach(fn, this, thisObj);
  };

if (!Array.prototype.filter)
  Array.prototype.filter = function (fn, thisObj) {
	 return window.filter(fn, this, thisObj);
  };

Array.prototype.remove = function ( idx ){
  var i, tmp;
  for(i =0 ; i < this.length ; i++){
	 if ( i > idx){
		this[i-1] = this[i];
	 }
	 else if (i == idx){
		tmp = this[i];
	 }
  }
  this.pop();
  return tmp;
};


Array.prototype.contains = function( val ){
  for( var i=0 ; i < this.length ; i++ ){
	 if(this[i] == val){
		return true;
	 }
  }
  return false;
};

Array.prototype.removeItem = function ( object ){
  var i, tmp;
  var arr = [];
  while( this.length > 0 ){
	 tmp = this.shift();
	 if( tmp == object ) break;
	 arr.push(tmp);
  }
  while(arr.length > 0){
	 this.unshift(arr.pop());
  }
  return tmp;
};
	 
Array.prototype.indexOfValue = function( object ){
  for(var i=0; i < this.length ; i++){
	 if( this[i] == object ) return i;
  }
  return -1;
};


window.getChildElementByAttribute = function(startnode, attribName, attribValue){
  var visitNode = function(node){
	 if(node == null) return null;
	 var testVal = null;
	 if( node.getAttribute != null  && (testVal  = node.getAttribute(attribName)) != null ){
		if(attribValue != null){
		  if(attribValue == testVal){
			 return  node;
		  }
		}
		else{
		  return node;
		}
	 }
	 if( node.childNodes ){
		for(var i=0; i< node.childNodes.length ; i ++){
		  var x = visitNode(node.childNodes[i]); 
		  if( x != null) return x;
		}
	 }
	 return null;
  }
  return visitNode(startnode);
}


  
  document.getElementByAttribute = function(attribName, attribValue){
	 return window.getChildElementByAttribute(document, attribName, attribValue);
  };
  

window.getChildElementsByAttribute = function(startnode, attribName, attribValue){
  var acc = [];
  var visitNode = function(node){
	 if(node == null) return null;
	 var testVal = null;
	 if( node.getAttribute != null  && (testVal  = node.getAttribute(attribName)) != null ){
		if(attribValue != null){
		  if(attribValue == testVal){
			 acc.push(node);
		  }
		}
		else{
		  acc.push(node);
		}
	 }
	 if( node.childNodes ){
		for(var i=0; i< node.childNodes.length ; i ++){
		  visitNode(node.childNodes[i]); 
		}
	 }
	 return null;
  };
  visitNode( startnode );
  return acc;
}
  document.getElementsByAttribute = function(attribName, attribValue){
	 return window.getChildElementsByAttribute(document, attribName, attribValue);
  };

/* parseUri JS v0.1, by Steven Levithan (http://badassery.blogspot.com)
Splits any well-formed URI into the following parts (all are optional):
----------------------
• source (since the exec() method returns backreference 0 [i.e., the entire match] as key 0, we might as well use it)
• protocol (scheme)
• authority (includes both the domain and port)
    • domain (part of the authority; can be an IP address)
    • port (part of the authority)
• path (includes both the directory path and filename)
    • directoryPath (part of the path; supports directories with periods, and without a trailing backslash)
    • fileName (part of the path)
• query (does not include the leading question mark)
• anchor (fragment)
*/
function parseUri(sourceUri){
    var uriPartNames = ["source","protocol","authority","domain","port","path","directoryPath","fileName","query","anchor"];
    var uriParts = new RegExp("^(?:([^:/?#.]+):)?(?://)?(([^:/?#]*)(?::(\\d*))?)?((/(?:[^?#](?![^?#/]*\\.[^?#/.]+(?:[\\?#]|$)))*/?)?([^?#/]*))?(?:\\?([^#]*))?(?:#(.*))?").exec(sourceUri);
    var uri = {};
    
    for(var i = 0; i < 10; i++){
        uri[uriPartNames[i]] = (uriParts[i] ? uriParts[i] : "");
    }
    
    // Always end directoryPath with a trailing backslash if a path was present in the source URI
    // Note that a trailing backslash is NOT automatically inserted within or appended to the "path" key
    if(uri.directoryPath.length > 0){
        uri.directoryPath = uri.directoryPath.replace(/\/?$/, "/");
    }
    
    return uri;
}

/*
  The following code is Copyright (C) Simon Willison 2004.
  ---------------------------------------------
  On 11 Aug 2005, at 00:05, Russ Tyndall wrote:

  > What is the license for this?

  BSD.

  Cheers,
	
  Simon
  ---------------------------------------------
  document.getElementsBySelector(selector)
  - returns an array of element objects from the current document
  matching the CSS selector. Selectors can contain element names, 
  class names and ids and can be nested. For example:
     
  elements = document.getElementsBySelect('div#main p a.external')
     
  Will return an array of all 'a' elements with 'external' in their 
  class attribute that are contained inside 'p' elements that are 
  contained inside the 'div' element which has id="main"

  New in version 0.4: Support for CSS2 and CSS3 attribute selectors:
  See http://www.w3.org/TR/css3-selectors/#attribute-selectors

  Version 0.4 - Simon Willison, March 25th 2003
  -- Works in Phoenix 0.5, Mozilla 1.3, Opera 7, Internet Explorer 6, Internet Explorer 5 on Windows
  -- Opera 7 fails 
*/

(function(){
  var getAllChildren = function(e) {
	 // Returns all children of element. Workaround required for IE5/Windows. Ugh.
	 return e.all ? e.all : e.getElementsByTagName('*');
  }
  document.getElementsBySelector = function(selector) {
	 // Attempt to fail gracefully in lesser browsers
	 if (!document.getElementsByTagName) {
		return new Array();
	 }
	 // Split selector in to tokens
	 var tokens = selector.split(' ');
	 var currentContext = new Array(document);
	 for (var i = 0; i < tokens.length; i++) {
		var token = tokens[i].replace(/^\s+/,'').replace(/\s+$/,'');;
		if (token.indexOf('#') > -1) {
		  // Token is an ID selector
		  var bits = token.split('#');
		  var tagName = bits[0];
		  var id = bits[1];
		  var element = document.getElementById(id);
		  if (tagName && element && element.nodeName.toLowerCase() != tagName) {
			 // tag with that ID not found, return false
			 return new Array();
		  }
		  // Set currentContext to contain just this element
		  currentContext = new Array(element);
		  continue; // Skip to next token
		}
		if (token.indexOf('.') > -1) {
		  // Token contains a class selector
		  var bits = token.split('.');
		  var tagName = bits[0];
		  var className = bits[1];
		  if (!tagName) {
			 tagName = '*';
		  }
		  // Get elements matching tag, filter them for class selector
		  var found = new Array;
		  var foundCount = 0;
		  for (var h = 0; h < currentContext.length; h++) {
			 var elements;
			 if (tagName == '*') {
            elements = getAllChildren(currentContext[h]);
			 } else {
            elements = currentContext[h].getElementsByTagName(tagName);
			 }
			 for (var j = 0; j < elements.length; j++) {
				found[foundCount++] = elements[j];
			 }
		  }
		  currentContext = new Array;
		  var currentContextIndex = 0;
		  for (var k = 0; k < found.length; k++) {
			 if (found[k].className && found[k].className.match(new RegExp('\\b'+className+'\\b'))) {
				currentContext[currentContextIndex++] = found[k];
			 }
		  }
		  continue; // Skip to next token
		}
		// Code to deal with attribute selectors
		if (token.match(/^(\w*)\[(\w+)([=~\|\^\$\*]?)=?"?([^\]"]*)"?\]$/)) { 
      var tagName = RegExp.$1;
      var attrName = RegExp.$2;
      var attrOperator = RegExp.$3;
      var attrValue = RegExp.$4;
      if (!tagName) {
        tagName = '*';
      }
      // Grab all of the tagName elements within current context
      var found = new Array;
      var foundCount = 0;
      for (var h = 0; h < currentContext.length; h++) {
        var elements;
        if (tagName == '*') {
            elements = getAllChildren(currentContext[h]);
        } else {
            elements = currentContext[h].getElementsByTagName(tagName);
        }
        for (var j = 0; j < elements.length; j++) {
          found[foundCount++] = elements[j];
        }
      }
      currentContext = new Array;
      var currentContextIndex = 0;
      var checkFunction; // This function will be used to filter the elements
      switch (attrOperator) {
        case '=': // Equality
          checkFunction = function(e) { return (e.getAttribute(attrName) == attrValue); };
          break;
        case '~': // Match one of space seperated words 
          checkFunction = function(e) { return (e.getAttribute(attrName).match(new RegExp('\\b'+attrValue+'\\b'))); };
          break;
        case '|': // Match start with value followed by optional hyphen
          checkFunction = function(e) { return (e.getAttribute(attrName).match(new RegExp('^'+attrValue+'-?'))); };
          break;
        case '^': // Match starts with value
          checkFunction = function(e) { return (e.getAttribute(attrName).indexOf(attrValue) == 0); };
          break;
        case '$': // Match ends with value - fails with "Warning" in Opera 7
          checkFunction = function(e) { return (e.getAttribute(attrName).lastIndexOf(attrValue) == e.getAttribute(attrName).length - attrValue.length); };
          break;
        case '*': // Match ends with value
          checkFunction = function(e) { return (e.getAttribute(attrName).indexOf(attrValue) > -1); };
          break;
        default :
          // Just test for existence of attribute
          checkFunction = function(e) { return e.getAttribute(attrName); };
      }
      currentContext = new Array;
      var currentContextIndex = 0;
      for (var k = 0; k < found.length; k++) {
        if (checkFunction(found[k])) {
          currentContext[currentContextIndex++] = found[k];
        }
      }
      // alert('Attribute Selector: '+tagName+' '+attrName+' '+attrOperator+' '+attrValue);
      continue; // Skip to next token
    }
    
    if (!currentContext[0]){
    	return null;
    }
    
    // If we get here, token is JUST an element (not a class or ID selector)
    tagName = token;
    var found = new Array;
    var foundCount = 0;
    for (var h = 0; h < currentContext.length; h++) {
      var elements = currentContext[h].getElementsByTagName(tagName);
      for (var j = 0; j < elements.length; j++) {
        found[foundCount++] = elements[j];
      }
    }
    currentContext = found;
  }
  return currentContext;
}

/* That revolting regular expression explained 
/^(\w+)\[(\w+)([=~\|\^\$\*]?)=?"?([^\]"]*)"?\]$/
											  \---/  \---/\-------------/    \-------/
											  |      |         |               |
											  |      |         |           The value
											  |      |    ~,|,^,$,* or =
											  |   Attribute 
											  Tag
											  */
											  })();
											  


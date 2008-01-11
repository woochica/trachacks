/* -*- Mode: javascript; -*- */
if(typeof(ADW) == 'undefined')ADW = {};
if(!ADW.Controls)
   ADW.Controls = {};

(function (){
   var Controls = ADW.Controls;

   Controls._createdNodes = {};
   Controls.setAttribute = function(node, attrib, value){
      if(typeof(value) == "function") node[attrib] = value;

      var test = attrib.toLowerCase();
      if(document.all){ //are we in IE, if so prepare for crack	
	 if(test	== 'class') node.className = value; //IE wont render styles based on attributes
	 else if(test == 'colspan') node.colSpan = value;
	 else if(test == 'valign') node.vAlign = value;
	 else if(test == 'rowspan') node.rowSpan = value;
	 else if(test == 'style') node.style.cssText = value;
	 else if(test == 'checked') node.checked = value;
	 else if(test == 'value') node.value = value;
	 else node.setAttribute( attrib , value );
      }
      else{
	 if(test == 'value') node.value = value;
	 node.setAttribute( attrib , value );
      }
   };
	
   Controls._createNode = function(tagName){
      return document.createElement(tagName);
   }

   var cn; //quick reference for this file;
   Controls.createNode = cn = function( name, attribs ){
      if(!Controls._createdNodes[name]){ // This is supposed to be faster than creating the node
	 Controls._createdNodes[name] = document.createElement(name);		
      }
      var _node = Controls._createdNodes[name].cloneNode(true);
      var setAttr = Controls.setAttribute;
      if( attribs ){
	 for( var item in attribs ){
	    setAttr(_node, item, attribs[item]);
	 }
      }
      var append = function( toApp ){
	 if(toApp.constructor && toApp.constructor == Array){
	    var kid;
	    for(var i=0 ; kid = toApp[i] ; i++) append(kid);
	 }
	 else
	    _node.appendChild(toApp);
      }
      for( var i=2 ; i < arguments.length ; i++ ){
	 var _x = arguments[i];
	 var hasHTMLEscape;
	 if( typeof(_x) == 'string' || ( _x.constructor && _x.constructor == String) ){
	    hasHTMLEscape = _x.indexOf('&')>0;
	    _x = document.createTextNode(_x);
	    _node.appendChild(_x);
	    // Replaces any thing that it escaped with it original escape charcters
	    if(_node.innerHTML){
	       _node.innerHTML = _node.innerHTML.replace(/&amp;/igm, '&');
	    }
	 }
	 else append(_x);
      }
      return _node;
   };

   Controls.findChildContainer = function ( arrOfNodes ){
      if( !arrOfNodes.length ){ // If we dont have a node list we should
	 arrOfNodes = [ arrOfNodes ];
      }
      for(var i=0 ; i < arrOfNodes.length ; i++){
	 var node = arrOfNodes[i];
	 var n = window.getChildElementByAttribute( node, 'childcontainer' );
	 if(n) return n;
      }
      return null;
   };


   //Clear the node of children
   Controls.clearChildNodes = 
      Controls.clearNodeChildren = function(node, tagName){
      if(!node)
		  return;
		  
      var l = node.childNodes.length;
      while( l != 0 ){
			var n = node.childNodes[0];
		   
		   if(!tagName || n.tagName == tagName)
				node.removeChild( n );
			
			l--;
		}
   };

   Controls.RegisterOnLoadEvents = function(){
      AddEventListener(window, 
		       'load', 
		       function(){
			  var arr = document.getElementByAttribute('onload');
			  for(var i=0; i < arr.length ;i++){
			     try{
				(function(){
				   eval( arr[i].getAttribute('onload') );
				}).call(this);
			     }
			     catch(Ex){
				Ex.ControlAffected = arr[i];
				throw EX
				   }
			  }
		       })
   };

   if(!Controls.PopularNodes)
      Controls.PopularNodes = {};

   Controls.PopularNodes.hiddenInput =function (name, value) {
      return cn("input", {type:'hidden', name:name, value:value});
   };
	
})();

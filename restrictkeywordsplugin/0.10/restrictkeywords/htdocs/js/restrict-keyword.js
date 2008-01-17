/*
* Copyright (C) 2008 Thomas Tressieres <thomas.tressieres@free.fr>
*
* ContentLoader class from Ajax in action book
*/

var plusImage;
var minusImage;
var treeUlCounter = 0;
var nodeId = 1;

var net = new Object();

net.ContentLoader=function( component, url, method, requestParams ) {
   this.component     = component;
   this.url           = url;
   this.requestParams = requestParams;
   this.method        = method;
}

net.ContentLoader.prototype = {
   getTransport: function() {
      var transport;
      if ( window.XMLHttpRequest )
         transport = new XMLHttpRequest();
      else if ( window.ActiveXObject ) {
         try {
            transport = new ActiveXObject('Msxml2.XMLHTTP');
         }
         catch(err) {
            transport = new ActiveXObject('Microsoft.XMLHTTP');
         }
      }
      return transport;
   },
   syncRequest: function(newUrl, params) {
      var requestParams = []
      requestParams.push(params);

      var oThis = this;
      var request = this.getTransport();
      newUrl = newUrl ? newUrl : this.url;
      request.open( this.method, newUrl, false );
      request.setRequestHeader( 'Content-Type', 'application/x-www-form-urlencoded');
      request.send( params );
      return request.responseText;
  }
};

function find_keywords_edit() {
    var key = document.getElementById('keywords');
    return key
}

function add_restrictkeywords_button(env) {
    var butt = document.createElement('button');
    butt.setAttribute('type', 'button');
    var buttext = document.createTextNode('...');
	butt.appendChild(buttext);
	butt.onclick = displayTree;
    var old_key = find_keywords_edit();

    old_key.setAttribute('readonly', 'true');
    old_key.parentNode.appendChild(butt);

    plusImage = 'chrome/rk_htdoc/images/tree-plus.gif';
    minusImage = 'chrome/rk_htdoc/images/tree-minus.gif';

    //request content to Trac Plugin
    this.ajax = new net.ContentLoader(this, env, 'GET', '');
    var data = this.ajax.syncRequest(env, '');

    // Insert content
    var globalDiv = document.createElement('div');
    globalDiv.setAttribute('id', 'keyword_tree_div');
    globalDiv.setAttribute('style', 'position:absolute; display:none; '+
                           'border: 1px solid #000000; overflow:auto; ' +
                           'background-color:#e0e0e0; left:0px; top:0px; width:450px; height:670px;');
    globalDiv.innerHTML=data;
    old_key.parentNode.appendChild(globalDiv);
}

function displayTree(e)
{
	if (!e) var e = window.event;
    var x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft - 200;
    var y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop - 550;
    var div = document.getElementById('keyword_tree_div');
    div.style.left = x + 'px';
    div.style.top = y + 'px';
    div.style.display = 'block';
}

function expandAll(treeId)
{
	var menuItems = document.getElementById(treeId).getElementsByTagName('LI');
	for(var no=0;no<menuItems.length;no++){
		var subItems = menuItems[no].getElementsByTagName('UL');
		if(subItems.length>0 && subItems[0].style.display!='block'){
			showHideNode(false,menuItems[no].id.replace(/[^0-9]/g,''));
		}
	}
}

function collapseAll(treeId)
{
	var menuItems = document.getElementById(treeId).getElementsByTagName('LI');
	for(var no=0;no<menuItems.length;no++){
		var subItems = menuItems[no].getElementsByTagName('UL');
		if(subItems.length>0 && subItems[0].style.display=='block'){
			showHideNode(false,menuItems[no].id.replace(/[^0-9]/g,''));
		}
	}
}

function toKeywordsString(treeId)
{
    var myText='';
	var menuItems = document.getElementById(treeId).getElementsByTagName('input');
	for(var no=0;no<menuItems.length;no++){
		if (menuItems[no].checked){
			myText += menuItems[no].id;
			myText += ' ';
		}
	}
	return myText;
}

function fromKeywordsString(treeId, keywords)
{
    var keys = keywords.split(' ');
    for(var no=0;no<keys.length;no++){
        var menuItem = document.getElementById(keys[no]);
        if (menuItem) {
            menuItem.checked = true;
            var myNode = menuItem.parentNode.parentNode;
            while (myNode && myNode.id) {
                showNode(myNode.id.replace(/[^0-9]/g,''));
                myNode = myNode.parentNode;
                if (myNode) myNode = myNode.parentNode; else break;
            }
        }
    }
}

function showHideNode(evt, inputId)
{
	if(inputId){
		if(!document.getElementById('keywordsTreeNode'+inputId))return;
		thisNode = document.getElementById('keywordsTreeNode'+inputId).getElementsByTagName('IMG')[0]; 
	}else {
		thisNode = this;
		if(this.tagName=='A')thisNode = this.parentNode.getElementsByTagName('IMG')[0];	
	}
	if(thisNode.style.visibility=='hidden')return;
	var parentNode = thisNode.parentNode;
	inputId = parentNode.id.replace(/[^0-9]/g,'');
	if(thisNode.src.indexOf(plusImage)>=0){
		thisNode.src = thisNode.src.replace(plusImage,minusImage);
		var ul = parentNode.getElementsByTagName('UL')[0];
		ul.style.display='block';
	}else{
		thisNode.src = thisNode.src.replace(minusImage,plusImage);
		parentNode.getElementsByTagName('UL')[0].style.display='none';
	}
	return false;
}

function showNode(inputId)
{
	if(inputId){
		if(!document.getElementById('keywordsTreeNode'+inputId))return;
		thisNode = document.getElementById('keywordsTreeNode'+inputId).getElementsByTagName('IMG')[0]; 
	}else {
		return;
	}
	if(thisNode.style.visibility=='hidden')return;
	var parentNode = thisNode.parentNode;
	inputId = parentNode.id.replace(/[^0-9]/g,'');
	if(thisNode.src.indexOf(plusImage)>=0){
		thisNode.src = thisNode.src.replace(plusImage,minusImage);
		var ul = parentNode.getElementsByTagName('UL')[0];
		ul.style.display='block';
	}
}

function initTree(idOfFolderTree)
{
	var dhtmlgoodies_tree = document.getElementById(idOfFolderTree);
	var menuItems = dhtmlgoodies_tree.getElementsByTagName('LI');	// Get an array of all menu items
	for(var no=0;no<menuItems.length;no++){
		nodeId++;
		var subItems = menuItems[no].getElementsByTagName('UL');
		var img = document.createElement('IMG');
		img.src = plusImage;
		img.onclick = showHideNode;
		if(subItems.length==0)
		    img.style.visibility='hidden';
		else{
			subItems[0].id = 'tree_ul_' + treeUlCounter;
			treeUlCounter++;
		}
		var aTag = menuItems[no].getElementsByTagName('A')[0];
		aTag.onclick = showHideNode;
		menuItems[no].insertBefore(img,aTag);
		if(!menuItems[no].id)
		    menuItems[no].id = 'keywordsTreeNode' + nodeId;
	}
}

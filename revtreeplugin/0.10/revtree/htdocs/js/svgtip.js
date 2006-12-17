/*
 * JTip
 * By Cody Lindley (http://www.codylindley.com)
 * Under an Attribution, Share Alike License
 * JTip is built on top of the very light weight jquery library.
 *
 * Badly hacked & tweaked to support XHTML/XML and SVG for the RevtreePlugin
 *   <emmanuel.blot@free.fr>
 */

$(document).ready(JT_init);

function JT_init(){
    $('a[@id^=rev]')
    .hover(function(){JT_show(this)},function(){JT_hide(this)})
      .click(function(){return false});     
}

function JT_hide(object) {
   $('#JT').remove()
}

function JT_show(object) {
  var href = 'href';
  if (! jQuery.browser.opera) { href = 'xlink:' + href; }
  var url = object.getAttribute(href);
  var id = object.getAttribute('id');
  var title = id.replace(/^rev/, 'Changeset ');
  var box = getSvgPosition(id);
  if(title == false)title=' ';
  var de = document.documentElement;
  var w = self.innerWidth || (de&&de.clientWidth) || document.body.clientWidth;
  var hasArea = w - box.x;
  var clickElementy = box.y+8;
  var queryString = url.replace(/^[^\?]+\??/,'');
  var params = parseQuery( queryString );
  if(params['width'] === undefined){params['width'] = 250};
  if(params['link'] !== undefined){     
  $(object).bind('click',function(){window.location = params['link']});
  //$(object).css('cursor','pointer');
  }
    
  if(hasArea>((params['width']*1)+box.w)){
     var arrowOffset = box.w + 11;
     var clickElementx = box.x + arrowOffset + 3;
     var side = 'left';
  } else {
     var clickElementx = box.x - ((params['width']*1) + 15) - 3;
     var side = 'right';
  }

  var ns = "http://www.w3.org/1999/xhtml";
  var d0=document.createElementNS(ns,"div");
  d0.setAttribute("id","JT");
  d0.setAttribute("style", "width:"+params['width']*1+"px; " +
                           "left:"+clickElementx+"px; " +
                           "top:"+clickElementy+"px");
  var d1=document.createElementNS(ns,"div");
  d1.setAttribute("id","JT_arrow_"+side);
  if ( side == 'right' ) {
     d1.setAttribute("style", "left:"+((params['width']*1)+1)+"px");
  }
  var d2=document.createElementNS(ns,"div");
  d2.setAttribute("id","JT_close_"+side);
  d2.appendChild(document.createTextNode(title));
  var d3=document.createElementNS(ns,"div");
  d3.setAttribute("id","JT_copy");
  var d4=document.createElementNS(ns,"div");
  d4.setAttribute("id","JT_loader");
  d3.appendChild(d4);
  d0.appendChild(d1);
  d0.appendChild(d2);
  d0.appendChild(d3);

  document.getElementsByTagName('body')[0].appendChild(d0);

  // netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
  $('#JT').show();
  $('#JT_copy').load(url);
}

function getSvgPosition(objectId) {
   var svg = document.getElementsByTagName('svg')[0];
   var anodes = svg.getElementsByTagName('a');
   var object;
	for ( var e = 0; e < anodes.length; e++ ) {
      if ( anodes[e].getAttribute('id') == objectId ) {
         object = anodes[e];
         break;
      }
   }
   var cnodes = object.childNodes
   var elem;
	for ( var n = 0; n < cnodes.length; n++ ) {
      if ( cnodes[n].tagName == "g" ) {
         elem = cnodes[n]
         break;
      } 
   }
   var box = elem.getBBox();
   var matrix = svg.getScreenCTM();
   var p1 = svg.createSVGPoint();
   var p2 = svg.createSVGPoint();
   p1.x = box.x;
   p1.y = box.y;
   p2.x = p1.x + box.width;
   p2.y = p1.y + box.height;
   p1 = p1.matrixTransform(matrix);
   p2 = p2.matrixTransform(matrix);
   var r = Object();
   r.x = Math.floor(p1.x)+posLeft();
   r.y = Math.floor(p1.y)+posTop();
   r.w = Math.floor(p2.x-p1.x);
   r.h = Math.floor(p2.y-p1.y);
   return r;
}

function posLeft() {
   return typeof window.pageXOffset != 'undefined' ? 
      window.pageXOffset :
      document.documentElement && 
         document.documentElement.scrollLeft ? 
            document.documentElement.scrollLeft : 
            document.body.scrollLeft ? document.body.scrollLeft : 0; 
}
 
function posTop() {
   return typeof window.pageYOffset != 'undefined' ?  
      window.pageYOffset : 
      document.documentElement && 
         document.documentElement.scrollTop ? 
            document.documentElement.scrollTop : 
            document.body.scrollTop ? document.body.scrollTop : 0;
} 

function parseQuery (query) {
  var Params = new Object ();
  if ( ! query ) return Params; // return empty object
  var Pairs = query.split(/[;&]/);
  for ( var i = 0; i < Pairs.length; i++ ) {
     var KeyVal = Pairs[i].split('=');
     if ( ! KeyVal || KeyVal.length != 2 ) continue;
     var key = unescape( KeyVal[0] );
     var val = unescape( KeyVal[1] );
     val = val.replace(/\+/g, ' ');
     Params[key] = val;
  }
  return Params;
}

function blockEvents(evt) {
  if(evt.target){
    evt.preventDefault();
  }else{
    evt.returnValue = false;
  }
}

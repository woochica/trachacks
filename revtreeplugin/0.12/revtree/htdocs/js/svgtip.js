/*
 * JTip
 * By Cody Lindley (http://www.codylindley.com)
 * Under an Attribution, Share Alike License
 * JTip is built on top of the very light weight jquery library.
 *
 * Badly hacked & tweaked to support XHTML/XML and SVG for the RevtreePlugin
 * by Emmanuel Blot <emmanuel.blot@free.fr> 2006-2008
 *
 * You might wonder why the hell regular Javascript functions are mixed with
 * jQuery ones... The trouble is that JQuery exhibits many difficulties with
 * XML documents for now (jQuery 1.2.3) and is sometimes unable to cope with
 * XML+SVG document. The funny part is that code that works on some browsers
 * (Presto, Webkit for ex.) does not work with the lastest releases of Gecko,
 * and vice-versa.  
 */

var jttimer = null;

(function($){
    
window.JT_get_svganchors = function() {
  if ( (jQuery.browser.mozilla && 
        (parseFloat(jQuery.browser.version) < 1.9)) ||
        (jQuery.browser.safari && 
              (parseFloat(jQuery.browser.version) < 523)) ) {
    // Firefox 1.x, 2.x, OmniWeb 5.x
    var vanchors = [];
    jQuery.each($('a[@id^=rev]'), function(index, value) {
      vanchors.push(value);
    });
    return vanchors;
  }
  else {
    // Firefox 3.x, Opera, Safari, ...
    var anchors;
    anchors = document.getElementsByTagNameNS('http://www.w3.org/2000/svg', 
                                              'a');
    var vanchors = [];
    for(var i in anchors) {
      if ( anchors[i].id && anchors[i].id.substring(0, 3) == 'rev' ) {
          vanchors.push(anchors[i]);
      }
    }
    return vanchors;
  }
}

window.JT_init = function(){
  var anchors = JT_get_svganchors();
  for (var n = 0; n < anchors.length; n++){
    jQuery(anchors[n]).hover(
           function(){JT_show(this)},
           function(){jttimer=setTimeout("JT_remove();", 250);}
    );
  }
}

window.JT_cancel = function() {
  if (jttimer) {
    clearTimeout(jttimer);
    jttimer = null;
  }
}

window.JT_remove = function() {
  var jt = $('#JT');
  if ( jt ) { jt.remove(); }
  var jt_connect = $('#JT_connect');
  if ( jt_connect ) { jt_connect.remove(); }
}

window.JT_hide = function() {
   JT_cancel();
   JT_remove();
}

window.JT_show = function(object) {
  if ( $('#JT') ) {
     JT_hide();
  }
  var href = 'href';
  if (! jQuery.browser.opera) { href = 'xlink:' + href; }
  var url = object.getAttribute(href);
  var logurl = url.replace(/\/changeset\//, '/revtree_log/');
  var id = object.getAttribute('id');
  var style = object.getAttribute('style');
  var colors = style.split(';')
  var fgc = colors[0].replace(/^.*color:/,'');
  var bgc = colors[1].replace(/^.*color:/,'');
  var rev = id.replace(/^rev/, '');
  var box = getSvgPosition(id);
  var de = document.documentElement;
  var w = self.innerWidth || (de&&de.clientWidth) || document.body.clientWidth;
  var hasArea = w - box.x;
  var clickElementy = box.y + (box.h/2);
  var tipw = 250;
    
  if( hasArea > (tipw+box.w) ) {
     var clickElementx = box.x + box.w + 20;
     var connectx = box.x + box.w;
     var side = 'left';
  } else {
     var clickElementx = box.x - tipw - 21;
     var connectx = box.x - 20;
     var side = 'right';
  }

  // cannot use jQuery .append() because the document type is 
  // application/xhtml+xml; need to use the verbose solution
  var ns = 'http://www.w3.org/1999/xhtml';
  var jt = document.createElementNS(ns, 'div');
  jt.setAttribute('id', 'JT');
  jt.setAttribute('style', 'width:' + tipw + 'px;' +
                           'left:' + clickElementx+'px;' +
                           'top:' + (clickElementy-13) + 'px;' +
                           'border: 2px solid ' + fgc);
  var jt_connect = document.createElementNS(ns, 'div');
  jt_connect.setAttribute('id', 'JT_connect');
  jt_connect.setAttribute('style', 'left:' + connectx + 'px; ' +
                                   'top:' + (clickElementy-1) + 'px; ' +
                                   'border: 2px solid ' + fgc);
  var jt_title = document.createElementNS(ns, 'div');
  jt_title.setAttribute('id', 'JT_title');
  jt_title.setAttribute('class', 'changeset');
  jt_title.setAttribute('style', 'background-color:' + bgc);
  var title = document.createElementNS(ns, 'span');
  title.appendChild(document.createTextNode('Changeset '));
  var titlelink = document.createElementNS(ns, 'a');
  titlelink.setAttribute('href', url);
  titlelink.appendChild(document.createTextNode('[' + rev +']'));
  title.appendChild(titlelink);
  jt_title.appendChild(title);
  var jt_copy = document.createElementNS(ns, 'div');
  jt_copy.setAttribute('id', 'JT_copy');
  var jt_loader = document.createElementNS(ns, 'div');
  jt_loader.setAttribute('id', 'JT_loader');
  var span2 = document.createElementNS(ns, 'span');
  span2.setAttribute('id', 'loading');
  var hellip = String.fromCharCode(8230);
  span2.appendChild(document.createTextNode('loading changeset info' + 
                                            hellip));
  jt_loader.appendChild(span2);
  jt_copy.appendChild(jt_loader);
  jt.appendChild(jt_title);
  jt.appendChild(jt_copy);
                           
  $('body').append(jt);
  $('body').append(jt_connect);

  $('#JT').hover(function() { JT_cancel(); }, function() { JT_remove(); });
  $('#JT_connect').show();
  $('#JT').show();
  // we want text result from the XHTML+XML server response for use 
  // wtih innerHTML, as load() does not work for some reason (why?)  
  // cannot use $.get(), need to go with $.ajax()
  $.ajax({async: true, type: "GET", dataType: 'text', 
          url: logurl, success: updateJT});
}

window.updateJT = function(data) {
  // cannot use innerHTML with jQuery ($('#JT_copy').innerHTML)
  var copy = document.getElementById('JT_copy');
  // why innerHTML work with application/xhtml+xml doctype here?
  copy.innerHTML = data;
}

window.getSvgPosition = function(objectId) {
  var svg = document.getElementById('svgbox');
  var anodes = JT_get_svganchors();
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
    if ( cnodes[n].tagName == "svg:g" ) {
      elem = cnodes[n]
      break;
    } 
  }
   
  var r = Object();
  var mx = svg.getScreenCTM();
  var box = elem.getBBox();
  var svgpos = findPos(svg);
  
  // Not sure who's right or wrong here: Gecko, Webkit, Presto, ...?
  // Anyway the following hack seems to work. Javascript, oh my...
  if ( jQuery.browser.opera || jQuery.browser.safari ) {
    r.x = Math.floor(box.x*mx.a)+svgpos[0];
    r.y = Math.floor(box.y*mx.d)+svgpos[1];
    r.w = Math.floor(box.width*mx.a);
    r.h = Math.floor(box.height*mx.d);
    return r;
  }
  else {
    var p1 = svg.createSVGPoint();
    var p2 = svg.createSVGPoint();
    p1.x = box.x;
    p1.y = box.y;
    p2.x = p1.x + box.width;
    p2.y = p1.y + box.height;
    p1 = p1.matrixTransform(mx);
    p2 = p2.matrixTransform(mx);
    r.x = Math.floor(p1.x)+posLeft();
    r.y = Math.floor(p1.y)+posTop();
    r.w = Math.floor(p2.x-p1.x);
    r.h = Math.floor(p2.y-p1.y);
    return r;
  }
}

window.findPos = function(obj) {
  var curleft = curtop = 0;
  if (obj.offsetParent) {
    curleft = obj.offsetLeft
    curtop = obj.offsetTop
    while (obj = obj.offsetParent) {
      curleft += obj.offsetLeft
      curtop += obj.offsetTop
    }
  }
  return [curleft,curtop];
}

window.posLeft = function() {
  return typeof window.pageXOffset != 'undefined' ? 
    window.pageXOffset :
    document.documentElement && 
      document.documentElement.scrollLeft ? 
        document.documentElement.scrollLeft : 
        document.body.scrollLeft ? document.body.scrollLeft : 0; 
}
 
window.posTop = function() {
  return typeof window.pageYOffset != 'undefined' ?  
    window.pageYOffset : 
    document.documentElement && 
      document.documentElement.scrollTop ? 
        document.documentElement.scrollTop : 
        document.body.scrollTop ? document.body.scrollTop : 0;
} 

})(jQuery);


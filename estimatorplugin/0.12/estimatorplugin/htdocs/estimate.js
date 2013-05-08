/* -*- js2-basic-offset:2 -*- */
var cn = ADW.Controls.createNode;

var numval = function(selector, root){
  var v = Number($.trim($(selector,root).val()));
  if(isNaN(v)) return 0;
  return v;
};

var ave_no_zero = function (x, y){
  if(x && y && x!=0 && y!=0){
    var val = (x+y)/2;
    return Math.round(val * 1000)/1000;
  }
  else if (x && x !=0) return x;
  else if (y && y !=0) return y;
  return 0;
};

var blinkFade = function(m){
  m = $(m);
  m.animate({opacity:1},10000);
  m.animate({opacity:0},1000, null, function(){m.remove();});
};

var message = function(m){
  m = $('<div class="message">'+m+'</div>');
  $("#messages").append(m);
  blinkFade(m);
};

var clearHistory = function(){
  if(typeof(localStorage) != 'undefined') localStorage.clear();
};

var clearPageHistory = function(){
  if(typeof(localStorage) == 'undefined') return ;
  var i, v, name;
  var names = ['lineItems', 'persistenceDate', 'tickets','rate', 'variability', 'communication'];
  for(i=0 ; name=names[i]; i++)
    localStorage.removeItem(window.location+'#'+name);
};

var resetPage = function(){
  if(!confirm("Are you sure you wish to permanently remove this data without saving?"))
    return false;
  $("#estimateBody tbody tr").remove();
  currentIdx = 400000000;
  lineItems = savedLineItems;
  $('#tickets').val(ticketDefault);
  $('#rate').val(rateDefault);
  $('#variability').val(variabilityDefault);
  $('#communication').val(communicationDefault);
  clearPageHistory();
  loadLineItems();
  return false;
};

var browserPersist = function(){ };
if(typeof(localStorage) != 'undefined'){
  browserPersist = function(key /*, value*/){
    key = window.location+'#'+key;
    if(arguments.length >= 2){
      var value = arguments[1];
      localStorage.setItem(key, value);
      return value;
    }
    else {
      var v = localStorage.getItem(key);
      return v;
    }
  };
}
else{
  $('div.reset').remove(); // remove this extra stuff, since the browser doesnt support it anyway
}

var persistenceDate = function (){
  return Number(browserPersist('persistenceDate'));
};

var saveEstimate = function(ctl){
  runCalculation(true);
  ctl = $(ctl);
  if(ctl.is('form')) ctl.submit();
  else ctl.parents('form').first().submit();
};

var persistPage = function(){
  browserPersist('persistenceDate', Math.floor(new Date().getTime()/1000));
  persistLineItems();
  browserPersist('tickets', $('#tickets').val());
  browserPersist('rate', $('#rate').val());
  browserPersist('variability', $('#variability').val());
  browserPersist('communication', $('#communication').val());
};
$(window).unload(persistPage);// persist before we leave

var loadPersistedPage = function(){
  // our persisted data is older than the saved data
  if( Number(lastSaved) >= persistenceDate() ){
    clearPageHistory();
    return;
  }
  var items = persistedLineItems();
  if(items) message("Loading unsaved data, dont forget to save");
  else return;
  // we have persisted items and they seem newer than the saved ones
  if(items && items.length > 0) lineItems = items;
  function loadPersistedFields(names){
    var i, v, name;
    for(i=0 ; v=browserPersist(name=names[i]); i++) if(v)$('#'+name).val(v);
  }
  loadPersistedFields(['tickets', 'rate', 'variability', 'communication']);
};

var persistLineItems = function(){
  var li;
  var preparedLineItems = [];
  $("#estimateBody tbody tr").each(
    function(idx) {
      var id = $(this).attr('rowid');
      preparedLineItems.push(
        {id:id,
         ordinal:$("#ordinal"+id, this).val(),
         description:$("#description"+id, this).val(),
         low:$.trim($("#low"+id, this).val()) || 0,
         high:$.trim($("#high"+id, this).val()) || 0
        });
    });
  // console.log("Saving preparedLineItems:", preparedLineItems);
  browserPersist('lineItems', JSON.stringify(preparedLineItems));
};

var persistedLineItems = function(){
  return JSON.parse(browserPersist('lineItems'));;
};


function enterMeansNothing(event){
   if(!event) event = window.event;
   if(event.keyCode == 13){
      return false;
   }
   return true;
}
function enterMeansNewRow(event){
   if(!event) event = window.event;
   if(event.keyCode == 13){
      var tr = newLineItem();
      tr.cells[0].firstChild.focus();
      tr.cells[0].firstChild.value="";
      return false;
   }
   return true;
}

function chromeCleanerPredicate ( node ){
   if(node && node.tagName){
      //its all text FF plugin adds chrome images
      if (node.tagName.toLowerCase() == "img" && node.src.search('chrome://') == 0) return false;
   }
   return true;
}

function evenDeeperClone(node /* pred */){
   //firefox 2 has a bug where it wont clone textarea values sometimes
   // Optional pred arg determines whether or not a node should be cloned
   var pred = arguments[1] || chromeCleanerPredicate;
   var kid, cloned;
   if (pred && !pred(node)) return null;
   var res = $(node).clone()[0];
   //Clone the actual current textarea value rather than what it started with
   $("textarea", node).each(function(){
     var x = $(this);
     $("textarea#"+x.attr('id'),res).val(x.val());
   });
   return res;
}

function swapUp(btn){
  var row = btn;
  while((row = row.parentNode).tagName != 'TR');
  row = $(row);
  $(row).prev().before(row);
  runCalculation();
}

function swapDown(btn){
  var row = btn;
  while((row = row.parentNode).tagName != 'TR');
  row = $(row);
  $(row).next().after(row);
  runCalculation();
}

function reOrdinalLineItemRows() {
  $('#estimateBody tbody tr').each(
    function (idx){
      var id = $(this).attr('rowid');
      $("#ordinal"+id,this).val(idx);
    });
}

var uid = function (lineitem, str){
   return str+lineitem.id;
};
var _uid = uid;// wrappable version;
var currentIdx = 400000000;
function lineItemRow (lineitem){
   var uid = function (str){
      return _uid(lineitem, str);
   };
   var valFn = function(str, def){
      if (lineitem[str]) return lineitem[str];
      else return def || "";
   };
   var  tarea;
   lineitem.id = lineitem.id || ++currentIdx;
   var tr = cn('tr', {'class':"line-item", "rowid": lineitem.id},
	     cn('td', {'class':'textarea-holder description-cell'},
		tarea=cn('textarea', {id:uid("description"), name:uid("description"),
				      style:"height: 68px; width:100%;", 'class':'item-description'},
                   valFn('description'))),
	     cn('td', {'class':'number', valign:'top'},
		cn('input', {id:uid('low'),name:uid('low'), type:'text', style:"width:80px;",
			     'class':'number', value: valFn('low'), onkeyup:'runCalculation()',
			     onkeydown:'return enterMeansNewRow(event)'})),
	     cn('td', {'class':'number',valign:'top'},
		cn('input', {id:uid('high'), name:uid('high'),type:'text', style:"width:80px;",
			     'class':'number',value: valFn('high'), onkeyup:'runCalculation()',
			     onkeydown:'return enterMeansNewRow(event)'})),
	     cn('td', {id:uid('ave'), 'class':"numberCell", valign:'top', style:"width:80px;"}),
	     cn('td', {id:uid('buttons'), 'class':'buttons',valign:'top'},
                cn('input', {id:uid('ordinal'), name:uid('ordinal'), type:'hidden', value: valFn('ordinal')}),
	        cn('button',{onclick:'removeLineItem(this);return false;', 'class':'delete'},
		'remove'),
		cn('button',{onclick:'swapUp(this);return false;', 'class':'up'},'&nbsp;'),
		cn('button',{onclick:'swapDown(this);return false;', 'class':'down'},'&nbsp;')));
   tr.item = lineitem;
   lineitem.row = tr;
   $(tarea).autoResize({extraSpace:20});
   return tr;
}

function newLineItem(){
   $('#estimateBody tbody tr').each(function(){
     var id = Number($(this).attr("rowid"));
     if(id > currentIdx) currentIdx = id;
   });
   var lineItem = {};
   var tr = lineItemRow(lineItem);
   $('#estimateBody tbody').append(tr);
   return tr;
}

function makeNumberAccessor(id, def){
   return function(){
      var str = $$(id).value.trim();
      if (str.length == 0) return def;
      var val = Number(str);
      if (isNaN(val)) return def;
      return val;
   };
}

var rate = makeNumberAccessor('rate', 1);
var variability = makeNumberAccessor('variability', 1);
var communication = makeNumberAccessor('communication', 1);

var numberWithCommas = function(x) {
  var parts = x.toString().split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return parts.join(".");
};

var _runCalcWait;
function runCalculation(immediate){
  reOrdinalLineItemRows();
  function calc (){
    var item, lowTotal=0, highTotal=0, lowAdjusted, highAdjusted,
      lowCost, highCost;
    $("#estimateBody tbody tr").each(function(){
      var tr= $(this);
      var rowid = tr.attr('rowid');
      var low = numval("#low"+rowid, tr);
      var high = numval("#high"+rowid, tr);
      lowTotal+=low;
      highTotal+=high;
      $("#ave"+rowid,tr).html( ave_no_zero(low, high));
    });
    var adjust = function(num){
      return Math.round(num*1000)/1000;
    };
    lowTotal = adjust(lowTotal);
    highTotal = adjust(highTotal);
    lowAdjusted = adjust(variability() * communication() * lowTotal);
    highAdjusted = adjust(variability() * communication() * highTotal);
    lowCost = adjust(rate() * lowAdjusted);
    highCost = adjust(rate() * highAdjusted);
    $('#lowTotal').html( lowTotal );
    $('#highTotal').html( highTotal );
    $('#aveTotal').html( ave_no_zero(lowTotal, highTotal) );
    $('#lowAdjusted').html( lowAdjusted );
    $('#highAdjusted').html( highAdjusted );
    $('#aveAdjusted').html( ave_no_zero(lowAdjusted, highAdjusted) );
    $('#lowCost').html( numberWithCommas(lowCost) );
    $('#highCost').html( numberWithCommas(highCost) );
    $('#aveCost').html( numberWithCommas(ave_no_zero(lowCost, highCost)) );
    preparePreview();
    persistPage();
  }
  // this just prevents us from spinning on this constantly
  if( _runCalcWait ) window.clearTimeout(_runCalcWait);
  if( immediate ) calc();
  else _runCalcWait = window.setTimeout( calc, 750 );
};

function removeLineItem( btn ){
   var row = btn.parentNode.parentNode;
   row.parentNode.removeChild(row);
   runCalculation();
}
function removeInputsAndIds(parent){
   $("input, textarea", parent).each(function(){ var x = $(this); x.parent().html(x.val()); });
   $("td.buttons", parent).remove();
   $("[id]",parent).each(function(){ $(this).removeAttr("id"); });
   $(parent).removeAttr("id");
   return parent;
}
function removeFirstRow( elem ){
  $(elem.rows[0]).remove();
  return elem;
}

function fillLines(o){
  var line; o.lines=[];
  while(o.text && o.text.length>0){
    line = "";
    var i = o.width;
    var nextLine = o.text.indexOf('\n');
    var explicitNewline = nextLine >= 0 && nextLine < i;
    var foundSpace=false;
    if(explicitNewline) i = nextLine;
    else if(i>o.text.length) i = o.text.length;
    else{
      while(!o.text[i].match(/\s/i)) i--;
      foundSpace=true;
    }
    line += o.text.substr(0,i);
    if(explicitNewline || foundSpace) i++;     // skip newlines/spaces that are now newlines
    o.text = o.text.substr(i);   // remove already process text
    // pad out to correct num of chars
    while( line.length < o.width )
      if (o.alignment == 'RIGHT') line = " "+line;
      else line += " ";

    o.lines.push(line);
  }
  return o;
}

function fillwith (width, c){
  var w,out="";
  width=width||10;
  c = c || " ";
  for(w=0 ; w < width ; w++)out+=c;
  return out;
}

function fillTexts(texts, widths, alignments){
  var parts=[], lineCnt=0, i, o;
  for( i=0 , o={} ; o.text=texts[i] ; i++, o={} ){
    o.width = widths[i] || 10;
    o.alignment = alignments[i];
    parts.push(fillLines(o));
  }
  var part, line, j,  w, out="", more=true;
  // splice the chunks of line together, while there are
  // more lines in any part
  //return parts;
  var limit=100;
  while(more && (limit-- > 0)){
    more = false;
    for(i=0; part = parts[i]; i++){
      line = part.lines.shift() || fillwith(o.width);
      out +=  line + " | ";
      more |= part.lines.length > 0;
    }
    out+="\n";
  }
  return out;
};

function cellTexts (cells){
  return cells.map(function(){
    var e = $(this);
    if(e.has('input,textarea').length>0) return e.find('input,textarea').val();
    return e.text();
  });
};
function prepareComment( ){
   var s = "\n";
   $('#estimateParams tr').each(function(){
       var texts = cellTexts($(this.cells));
       var widths = [16, 8];
       var alignments = ['RIGHT','RIGHT'];
       s += fillTexts(texts, widths, alignments);
   });
   s += fillwith(81, "_")+"\n";
   var foundFoot = false;
   $('#estimateBody tbody tr').each(function(){
     var texts = cellTexts($(this.cells).not(':last-child'));
     var widths = [40, 10, 10, 10];
     var alignments = ['LEFT','RIGHT','RIGHT','RIGHT'];
     s += fillTexts(texts, widths, alignments);
     s += fillwith(81, "-")+"\n";
   });
   s += fillwith(81, "_")+"\n";
   $('#estimateBody tfoot tr').each(function(){
     var texts = cellTexts($(this.cells).not(':last-child'));
     var widths = [40, 10, 10, 10];
     var alignments = ['RIGHT','RIGHT','RIGHT','RIGHT'];
     s += fillTexts(texts, widths, alignments);
   });
   s += fillwith(81, "_")+"\n";
   return s;
};

var ticketLinkRegex = /(\/ticket\/(?:\d+))/;
var base = window.location.toString().replace(/\/Estimate.*$/, '');
function linkifyTickets(estimateBody){
  var linkifyCell = function(){
    var el = $(this), h = el.html();
    el.html(h.replace(ticketLinkRegex, '<a href="'+base+'$1">$1</a>'));
  };
  $('.description-cell', estimateBody).each(linkifyCell);
  return estimateBody;
}

function preparePreview(){
  var preview = $('#estimateoutput');
  preview.empty().
    append(removeFirstRow(removeInputsAndIds(evenDeeperClone($$('estimateParams'))))).
    append(linkifyTickets(removeInputsAndIds(evenDeeperClone($$('estimateBody')))));
  var txtComment = prepareComment(preview[0]);
  // console.log(txtComment);
  $('#diffcomment').val( txtComment );
  $('#comment').val( preview.html() );
};

function loadLineItems() {
  // loadPersistedPage();
  var item;
  lineItems.sort(
    function(a,b) {
      if (a.ordinal < b.ordinal) {
        return -1;
      }
      if (a.ordinal > b.ordinal) {
        return 1;
      }
      else {
        return 0;
      }
    }
  );
  for(var i=0; item = lineItems[i] ; i++){
    var tr = lineItemRow(item);
    $('#estimateBody tbody').append(tr);
  }
  runCalculation();
};

// init Everything
$(function(){
    loadLineItems();
    if(lineItems.length == 0) newLineItem();
    if(saveImmediately){
      saveEstimate($('.estimate-form'));
    }
});


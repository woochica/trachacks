var cn = ADW.Controls.createNode;

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
      //if(typeof(console)!='undefined') console.log("Persisting:",key, arguments[1]);
      return value;
    }
    else {
      var v = localStorage.getItem(key);
      //if(typeof(console)!='undefined') console.log("Loading persisting:",key, v);
      return v;
    }
  };
}
else{
  $('div.reset').remove(); // remove this extra stuff, since the browser doesnt support it anyway
}

var persistenceDate = function (){
  return browserPersist('persistenceDate');
};

var saveEstimate = function(ctl){
  runCalculation();
  ctl.form.submit();
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
  if( Number(lastSaved) >= Number(persistenceDate()) ) return;
  var items = persistedLineItems();
  if(items) message("Loading unsaved data, dont forget to save");
  else return;
  // we have persisted items and they seem newer than the saved ones
  if(items && items.length > 0) lineItems = items;
  function loadPersistedFields(names){
    var i, v, name;
    for(i=0 ; v=browserPersist(name=names[i]); i++) if(v)$('#'+name).val(v);
  }
  loadPersistedFields(['tickets','rate', 'variability', 'communication']);
};

var persistLineItems = function(){
  var preparedLineItems = [];
  var li;
  var valueLi = function(id, row){
    var newli = {id:id};
    newli.description = $("#description"+id,row).val();
    newli.low = $("#low"+id,row).val();
    newli.high = $("#high"+id,row).val();
    return newli;
  };
  var i = 0;
  $("#estimateBody tbody tr").each(function(){
    var tr= $(this);
    var rowid = tr.attr('rowid');
    preparedLineItems[i++] = valueLi(rowid, tr);
  });
  browserPersist('lineItems', JSON.stringify(preparedLineItems));
};

var persistedLineItems = function(){
  return JSON.parse(browserPersist('lineItems'));;
};

var uid = function (lineitem, str){
   return str+lineitem.id;
};
var _uid = uid;// wrappable version;

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
  persistPage();
}
function swapDown(btn){
  var row = btn;
  while((row = row.parentNode).tagName != 'TR');
  row = $(row);
  $(row).next().after(row);
  persistPage();
}

function lineItemRow (lineitem){
   var uid = function (str){
      return _uid(lineitem, str);
   };
   var valFn = function(str){
      if (lineitem[str]) return lineitem[str];
      else return "";
   };
   var  tarea;
   var tr = cn('tr', {'class':"line-item", "rowid":lineitem.id},
	     cn('td', {'class':'textarea-holder'},
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
	        cn('button',{onclick:'removeLineItem(this);return false;', 'class':'delete'},
		'remove'),
		cn('button',{onclick:'swapUp(this);return false;', 'class':'up'},'&nbsp;'),
		cn('button',{onclick:'swapDown(this);return false;', 'class':'down'},'&nbsp;')));
   tr.item = lineitem;
   lineitem.row = tr;
   $(tarea).autoResize({extraSpace:20});
   return tr;
}
var currentIdx = 400000000;

function newLineItem(){
   $('#estimateBody tbody tr').each(function(){
     var id = Number($(this).attr("rowid"));
     if(id > currentIdx) currentIdx = id;
   });
   var lineItem = {id:++currentIdx};
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

var ave_no_zero = function (x, y){
   if(x!=0 && y!=0){
      var val = (x+y)/2;
      return Math.round(val * 1000)/1000;
   }
   else if (x !=0) return x;
   else return y;
};


var _runCalcWait;
function runCalculation(immediate){
  function calc (){
    var item, lowTotal=0, highTotal=0, lowAdjusted, highAdjusted,
      lowCost, highCost;
    $("#estimateBody tbody tr").each(function(){
      var tr= $(this);
      var rowid = tr.attr('rowid');
      var low = Number($("#low"+rowid,tr).val());
      var high = Number($("#high"+rowid,tr).val());
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
    $('#lowCost').html( lowCost );
    $('#highCost').html( highCost );
    $('#aveCost').html( ave_no_zero(lowCost, highCost) );
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

function prepareComment( preview ){
   var s = "";
   function walker ( node ){
      for (var i=0, kid ; kid = node.childNodes[i]; i++ ){
	 if(kid && kid.tagName){
	    var tn = kid.tagName.toLowerCase();
	    if (tn == 'table'){
	       var print_sep = false;
	       for(var row,j=0 ; row = kid.rows[j] ; j++){
		  if (row.className == "lineItemheader") print_sep = true;
		  if (row.className == "lineItemFooter") print_sep = false;
		  for(var cell, k=0 ; cell = row.cells[k] ; k++){
		     var val = (cell.textContent || cell.innerText);
		     if(val) s += val + ((k==0 && print_sep) ? "\n|  " :
					 (print_sep ? "  |  " : "\t"));
		  }
		  s += "\n";
		  if(print_sep)s+="---------------------------\n";
	       }
	       s += "\n";
	    }
	 }
      }
   }
   walker(preview);
   return s;
};

function preparePreview(){
  var preview = $('#estimateoutput');
  preview.empty().
    append(removeFirstRow(removeInputsAndIds(evenDeeperClone($$('estimateParams'))))).
    append(removeInputsAndIds(evenDeeperClone($$('estimateBody'))));
  $('#diffcomment').val( prepareComment(preview[0]));
  $('#comment').val( preview.html() );
};

function loadLineItems() {
  loadPersistedPage();
  var item;
  for(var i=0; item = lineItems[i] ; i++){
    var tr = lineItemRow(item);
    $('#estimateBody tbody').append(tr);
  }
  runCalculation();
};

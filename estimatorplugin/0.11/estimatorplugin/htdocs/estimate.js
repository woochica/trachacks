var cn = ADW.Controls.createNode;

var uid = function (lineitem, str){
   return str+lineitem.id;
}
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
}
function swapDown(btn){
  var row = btn;
  while((row = row.parentNode).tagName != 'TR');
  row = $(row);
  $(row).next().after(row);
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
   var tr = cn('tr', {'class':"line-item"},
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
   var lineItem = {id:currentIdx++};
   var tr = lineItemRow(lineItem);
   lineItems.push(lineItem);
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
}


function runCalculation(){
   var item, lowTotal=0, highTotal=0, lowAdjusted, highAdjusted,
      lowCost, highCost;
   for(var i=0; item = lineItems[i] ; i++){
      function uid(str){
	 return _uid(item, str);
      }
      var valFn = function(str){
	 return makeNumberAccessor(uid(str), 0)();
      };
      var low = valFn('low');
      var high = valFn('high');

      lowTotal+=low;
      highTotal+=high;
      $$(uid('ave')).innerHTML = ave_no_zero(low, high);
   }
   var adjust = function(num){
      return Math.round(num*1000)/1000;
   };
   lowTotal = adjust(lowTotal);
   highTotal = adjust(highTotal);
   lowAdjusted = adjust(variability() * communication() * lowTotal);
   highAdjusted = adjust(variability() * communication() * highTotal);
   lowCost = adjust(rate() * lowAdjusted);
   highCost = adjust(rate() * highAdjusted);
   $$('lowTotal').innerHTML = lowTotal;
   $$('highTotal').innerHTML = highTotal;
   $$('aveTotal').innerHTML = ave_no_zero(lowTotal, highTotal);
   $$('lowAdjusted').innerHTML = lowAdjusted;
   $$('highAdjusted').innerHTML = highAdjusted;
   $$('aveAdjusted').innerHTML = ave_no_zero(lowAdjusted, highAdjusted);
   $$('lowCost').innerHTML = lowCost;
   $$('highCost').innerHTML = highCost;
   $$('aveCost').innerHTML = ave_no_zero(lowCost, highCost);
   preparePreview();
};

function removeLineItem( btn ){
   var row = btn.parentNode.parentNode;
   lineItems.removeItem(row.item);
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
}

function preparePreview(){
   var preview = $$('estimateoutput');
   while(preview.childNodes.length > 0) preview.removeChild(preview.firstChild);
   preview.appendChild(removeFirstRow(removeInputsAndIds(evenDeeperClone($$('estimateParams')))));
   preview.appendChild(removeInputsAndIds(evenDeeperClone($$('estimateBody'))));
   //alert(prepareComment( preview ));
   $$('diffcomment').value = prepareComment( preview );
   $$('comment').value = preview.innerHTML;
}

function loadLineItems() {
   var item;
   for(var i=0; item = lineItems[i] ; i++){
      var tr = lineItemRow(item);
      $('#estimateBody tbody').append(tr);
   }
   runCalculation();
}



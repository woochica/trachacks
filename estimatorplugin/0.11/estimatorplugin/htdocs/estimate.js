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

function lineItemRow (lineitem){
   var uid = function (str){
      return _uid(lineitem, str);
   }
   var valFn = function(str){
      if (lineitem[str]) return lineitem[str];
      else return "";
   }

   var tr = cn('tr', {},
	     cn('td', {},
		cn('textarea', {id:uid("description"), name:uid("description"), cols:30, style:"height: 34px;"},
                   valFn('description'))),
	     cn('td', { valign:'top'},
		cn('input', {id:uid('low'),name:uid('low'), type:'text', style:"width:80px;", 
			 value: valFn('low'), onkeyup:'runCalculation()',
			 onkeydown:'enterMeansNewRow(event)'})),
	     cn('td', {valign:'top'},
		cn('input', {id:uid('high'), name:uid('high'),type:'text', style:"width:80px;",
			 value: valFn('high'), onkeyup:'runCalculation()',
			 onkeydown:'enterMeansNewRow(event)'})),
	     cn('td', {id:uid('ave'), 'class':"numberCell", valign:'top', style:"width:80px;"}),
	     cn('td', {id:uid('buttons'),valign:'top'},
	        cn('button',{onclick:'removeLineItem(this);return false;'},'remove')));
   tr.item = lineitem;
   lineitem.row = tr;
   return tr;
}
var currentIdx = 400000000;

function newLineItem(){
   var lineItem = {id:currentIdx++};
   var tr = lineItemRow(lineItem);
   lineItems.push(lineItem);
   var foot = $$('lineItemFooter');
   foot.parentNode.insertBefore(tr, foot);
   return tr;
}

function makeNumberAccessor(id, def){
   return function(){
      var str = $$(id).value.trim();
      if (str.length == 0) return def;
      var val = Number(str);
      if (isNaN(val)) return def;
      return val;
   }
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
      }
      var low = valFn('low');
      var high = valFn('high');

      lowTotal+=low;
      highTotal+=high;
      $$(uid('ave')).innerHTML = ave_no_zero(low, high);
   }
   var adjust = function(num){
      return Math.round(num*1000)/1000;
   }
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
   if(!parent.tagName) return;
   if (parent.id) parent.id = "";
   var name = parent.tagName.toLowerCase();
   if(name == "input" || name == "textarea"){
      parent.parentNode.innerHTML = parent.value;
   }
   else if (name == "button"){
      parent.parentNode.removeChild(parent);
   }
   else{
      for(var i=0 ; node = parent.childNodes[i] ;i++){
	 removeInputsAndIds(node);
      }
   }
   return parent;
}
function removeFirstRow( elem ){
   var nd = elem.firstChild;
   do{
      if(nd.tagName){
	 if(nd.tagName.toLowerCase() == 'tbody'){
	    nd = nd.firstChild;
	 }
	 if(nd.tagName.toLowerCase() == 'tr'){
	    nd.parentNode.removeChild(nd);
	    return elem;
	 }
      }
   }while(nd = nd.nextSibling);
   return elem;
}
function preparePreview(){
   var preview = $$('estimateoutput');
   while(preview.childNodes.length > 0) preview.removeChild(preview.firstChild);
   preview.appendChild(removeFirstRow(removeInputsAndIds($$('estimateParams').cloneNode(true))));
   preview.appendChild(removeInputsAndIds($$('estimateBody').cloneNode(true)));
   $$('comment').innerHTML = preview.innerHTML;
}

function loadLineItems() {
   var item;
   for(var i=0; item = lineItems[i] ; i++){
      var tr = lineItemRow(item);
      var foot = $$('lineItemFooter');
      foot.parentNode.insertBefore(tr, foot);
   }
   runCalculation();
}



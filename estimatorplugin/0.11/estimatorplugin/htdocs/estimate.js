var cn = ADW.Controls.createNode;

var uid = function (lineitem, str){
   return str+lineitem.id;
}
var _uid = uid;// wrappable version;

function lineItemRow (lineitem){
   var uid = function (str){
      return _uid(lineitem, str);
   }
   var valFn = function(str){
      if (lineitem[str]) return lineitem[str];
      else return "";
   }
   var $$ = document.getElementById;
   var tr = cn('tr', {},
	     cn('td', {},
		cn('textarea', {id:uid("description"), rows:2, cols:30},
                   valFn('description'))),
	     cn('td', { valign:'top'},
		cn('input', {id:uid('low'), type:'text', style:"width:80px;", 
			 value: valFn('low'), onkeyup:'runCalculation()'})),
	     cn('td', {valign:'top'},
		cn('input', {id:uid('high'), type:'text', style:"width:80px;"
			 , value: valFn('high'), onkeyup:'runCalculation()'})),
	     cn('td', {id:uid('ave'), valign:'top', style:"width:80px;"}),
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
}

function makeMultiplierAccessor(id){
   return function(){
      var str = $$(id).value.trim();
      if (str.length == 0) return 1;
      var val = Number(str);
      if (isNaN(val)) return 1;
      return val;
   }
}

var rate = makeMultiplierAccessor('rate');
var variability = makeMultiplierAccessor('variability');
var communication = makeMultiplierAccessor('communication');

var lineItemValue
function runCalculation(){
   var item, lowTotal=0, highTotal=0, lowAdjusted, highAdjusted,
      lowCost, highCost;
   for(var i=0; item = lineItems[i] ; i++){
      function uid(str){
	 return _uid(item, str);
      }
      var valFn = function(str){
	 var str = $$(uid(str)).value.trim();
	 if (str.length == 0) return 0;
	 var val = Number(str);
	 if (isNaN(val)) return 0;
	 return val;
      }
      var low = valFn('low');
      var high = valFn('high');

      lowTotal+=low;
      highTotal+=high;
      $$(uid('ave')).innerHTML = (low+high)/2;
   }
   lowAdjusted = variability() * communication() * lowTotal ;
   highAdjusted = variability() * communication() * highTotal ;
   lowCost = rate() * lowAdjusted;
   highCost = rate() * highAdjusted;
   $$('lowTotal').innerHTML = lowTotal;
   $$('highTotal').innerHTML = highTotal;
   $$('aveTotal').innerHTML = (lowTotal+highTotal) / 2;
   $$('lowAdjusted').innerHTML = lowAdjusted;
   $$('highAdjusted').innerHTML = highAdjusted;
   $$('aveAdjusted').innerHTML = (lowAdjusted+highAdjusted) / 2;
   $$('lowCost').innerHTML = lowCost;
   $$('highCost').innerHTML = highCost;
   $$('aveCost').innerHTML = (lowCost+highCost) / 2;
};

function removeLineItem( btn ){
   var row = btn.parentNode.parentNode;
   lineItems.removeItem(row.item);   
   row.parentNode.removeChild(row);
}

function loadLineItems( ){
   var item;
   for(var i=0; item = lineItems[i] ; i++){
      var tr = lineItemRow(item);
      var foot = $$('lineItemFooter');
      foot.parentNode.insertBefore(tr, foot);
   }
   runCalculation();
}



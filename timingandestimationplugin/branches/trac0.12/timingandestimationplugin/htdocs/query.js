$(document).ready(function(){
  // Fields we will total
  var columns = ['totalhours','estimatedhours'];
  var tbodies = $('table.listing.tickets tbody');

  tbodies.each(function(idx, tbody){
    tbody = $(tbody);
    if(tbody.has('tr.even').length == 0) return true;
    var tfoot = $('<tbody class="foot"></tbody>');
    var totalsRow = $('tr:first-child',tbody).clone();
    tfoot.append(totalsRow);

    // Build footer row
    $('td',totalsRow).empty()
      .css('background-color','#EEF')
      .css('text-align','right')
      .css('padding','0.1em 0.5em')
      .css('border','1px solid #DDD');

    $.each(columns,function(idx, field){
      // count totals
      var total = 0;
      $('td.'+field,tbody).each(function(cidx, cell){
	$(cell).css('text-align','right');
	var val = Number($(cell).text());
	if(!isNaN(val))total+=val;
      });

      //set total text in each footer row
      $('td.'+field,totalsRow).text(total.toString());
    });

    // attach footer row
    tbody.after(tfoot);
  });
});

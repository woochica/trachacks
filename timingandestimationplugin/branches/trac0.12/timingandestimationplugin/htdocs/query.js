$(document).ready(function(){
  // Fields we will total
  var columns = ['totalhours','estimatedhours'];
  var tbls = $('table.listing.tickets');
  tbls.each(function(idx, tbl){
    tbl = $(tbl);

    // Build footer row
    var tfoot = $('<tfoot></tfoot>');
    var totalsRow = $('tbody tr:first-child',tbl).clone();
    $('td',totalsRow).empty()
      .css('background-color','#EEF')
      .css('text-align','right')
      .css('padding','0.1em 0.5em')
      .css('border','1px solid #DDD');

    $.each(columns,function(idx, field){
      // count totals
      var total = 0;
      $('tbody td.'+field,tbl).each(function(cidx, cell){
	$(cell).css('text-align','right');
	var val = Number($(cell).text());
	if(!isNaN(val))total+=val;
      });

      //set total text in each footer row
      $('td.'+field,totalsRow).text(total.toString());
    });

    // attach footer row
    tfoot.append(totalsRow);
    tbl.append(tfoot);
  });
});

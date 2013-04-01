(function(){
var btnTemp = $('<div class="inlinebuttons"><input type="submit" title="add time elapsed since this comment" value="Add Time" class="add-hours-btn"></div>');

function add_buttons(){
  $(".change .trac-ticket-buttons").each(function(i,e){
    var ts = timestamp_from_change(this);
    var el = $(this);
    // we had a timestamp, but no add hours button
    if(ts && el.has('.add-hours-btn').length == 0) el.append(btnTemp.clone().click(
      function(){TandE_onClickOfADateElement(ts);}
    ));
  });
}

function timestamp_from_change(el){
  el = $(el);
  if(!el.is(".change")) el = $(el.parents(".change"));
  var id=el.attr("id"), r = /trac-change-\d+-(\d+)/,
    m = id && id.match(r),
    ts = m && m[1];
  if(ts) return new Date(Math.floor(Number(ts/1000)));
  return null;
}

function TandE_onClickOfADateElement(commenttime) {
  var now = new Date();
  var minutesDiff = (now - commenttime) / 1000 / 60;
  var fifteens = Math.floor(minutesDiff / 15);
  var remainder = minutesDiff % 15;
  var hours = (fifteens * 0.25) + ((remainder > 5) ? 0.25 : 0.0);
  $('#field-hours')[0].value = hours;
  return false;
}

// when we replace the changelog/timeline add buttons
$(document).ajaxStop(add_buttons);
$(document).ready(add_buttons);
})(); // end of scoping function
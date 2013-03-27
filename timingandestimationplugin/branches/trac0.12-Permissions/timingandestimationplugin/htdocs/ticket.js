(function(){
function float_to_hours_minutes(inp){
  var hours = Number($.trim(inp));
  if ( isNaN(hours) ) return inp;
  var whole_hours, mins, str, neg = false;
  if(hours < 0){
    neg = true;
    hours *= -1;
  }
  whole_hours = Math.floor(hours);
  mins = Math.floor((hours - whole_hours) * 60);
  str = neg ? '-' : '';
  if ( whole_hours > 0 ) str += whole_hours + 'h';
  if ( mins > 0 )  str += ' ' + mins + 'm';
  if( whole_hours == 0 && mins == 0 ) str = '0h';
  return str;
}


function TandE_ticket_ui_improvements (){
  var i,s,to_munge = ['#h_estimatedhours + td',
  '#h_totalhours + td',
  '.changes .trac-field-hours > em',
  '.changes .trac-field-totalhours > em',
  '.changes .trac-field-estimatedhours > em'];
  for(i=0 ; s= to_munge[i] ; i++){
    $(s).each(function(){ $(this).text(float_to_hours_minutes($(this).text())); });
  }
}

$(document).ready(TandE_ticket_ui_improvements);
})(); // end of scoping function











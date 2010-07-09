
$(document).ready(function(){
  // display modify ticket by default
  // window.setTimeout(function(){$("#modify").parent().removeClass("collapsed");}, 25);
  var tbl, hours, colClass, tr, replacement;
  tbl = $('<table style="border:1px solid #D7D7D7;" border="0" cellpadding="3" cellspacing="0"><tbody><tr></tr></tbody></table>');
  $('#comment').parent().append(tbl);
  hours = $('#field-hours');
  colClass = hours.parent().attr("class");
  tr = hours.parent().parent();
  $(tbl[0].rows[0]).append($('.'+colClass, tr));
  replacement = $('<td class="'+colClass+'"></td>');
  tr.prepend(replacement.clone()).prepend(replacement.clone());
});

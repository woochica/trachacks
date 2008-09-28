$(function() {
  var metanav = $('#metanav li');
  var last = metanav.eq(metanav.length - 1);
  last.removeClass('last');
  last.after('<li class="last"><a href="#" id="tracdeveloper-logbutton">Log</a></li>');
  $('#tracdeveloper-logbutton').click(function() {
    $('#tracdeveloper-log').toggle();
    return false;
  });
  
  $('#tracdeveloper-log').hide();
});
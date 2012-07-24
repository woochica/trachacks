$(function() {
  var last_note = null;
  
  // Look for inital status in the URL
  var init_note = /#FootNote(Ref)?(\d+)/.exec(window.location);
  if(init_note != null) {
    last_note = init_note[2];
    $('#FootNote'+last_note).addClass('footnote-active');
  }
  
  $('.footnote a').click(function() {
    if(last_note) {
      $('#FootNote'+last_note).removeClass('footnote-active');
    }
    var cur_note = $(this).attr('id').substr(11);
    last_note = cur_note;
    $('#FootNote'+cur_note).addClass('footnote-active');
  });
  
  $('.footnotes .sigil').click(function() {
    var cur_note = $(this).attr('href').substr(12);
    if(cur_note == last_note) {
      $('#FootNote'+last_note).removeClass('footnote-active');
      last_note = null;
    }
  });
});
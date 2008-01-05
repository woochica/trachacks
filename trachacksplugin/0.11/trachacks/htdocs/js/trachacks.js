$(document).ready(function() {
  // Move the label for each field into the info block.
  $('.info').each(function() {
  var info = this;
  var fieldid = info.id.slice(0, -4);

    $('label[@for="' + fieldid + '"]').each(function() {
    var title = $(this).text();

      $(info).prepend('<strong>' + title + '</strong>');
    });
  });

  // Fade all the info blocks out then focus the #name field
  $('.info').fadeTo('fast', 0.4, function() {
    $('#name').focus();
  });


  // Handle focus/blur of input fields
  $('input, textarea').focus(function() {
  var id = '#' + this.id + 'info';

    $(id).fadeTo('slow', 1.0);
  });
  $('input, textarea').blur(function() {
    $('#' + this.id + 'info').fadeTo('slow', 0.4);
  });
});

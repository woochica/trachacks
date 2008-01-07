$(document).ready(function() {
  // Move the label for each field into the hint block.
  $('.hint').each(function() {
  var hint = this;
  var fieldid = hint.id.slice(0, -4);

  });

  // Handle focus/blur of input fields
  $.fn.handleInfo = function(hint, label) {
    return this.each(function() {
    var hintid;

      if (hint == undefined)
        hintid = '#' + this.id + 'hint';
      else
        hintid = hint;

      hintid = $(hintid);

      $(hintid).hide();

      $(this).focus(function() { hintid.show(); });
      $(this).blur(function() { hintid.hide(); });

      if (hintid.attr('copied_label') == undefined) {
      var title = label;

        hintid.attr('copied_label', true);
        if (title == undefined) {
          $('label[@for="' + this.id + '"]').each(function() {
            title = $(this).text();
          });
        }
        hintid.prepend('<strong>' + title + '</strong>' + '<span class="hint-pointer">&nbsp;</span>');
      }
    });
  }

  $('#name, #title, #description, #installation').handleInfo();

  $('input[@name="type"]').handleInfo('#typehint', 'Type');
  $('input[@name="release"]').handleInfo('#releasehint', 'Compatibility');

  if (!$('input[@class="error"]:first').focus().size()) {
    $('#name').focus();
  }
});

/* Add helpers to tag cloud. */
var clean_tags = function(tags) {
var split = tags.replace(/^ +| +$/g, '').split(/ +/);

  split.sort();
  return split.join(' ');
};

/* Highlight tags from the mini-cloud that are in the tags field. */
var highlight_tags = function() {
var tags = clean_tags($('#tags').attr('value')).split(/ +/);

  $('#cloud a').each(function() {
    if (tags.indexOf($(this).text()) != -1) {
      $(this).css('background-color', 'yellow');
    } else {
      $(this).css('background-color', 'transparent');
    }
  });
};

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

      $(this).focus(function() { hintid.show(); return true; });
      $(this).blur(function() { hintid.hide(); return true; });

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

  // Add hints to controls.
  $('#name, #title, #description, #installation, #tags').handleInfo();

  $('#cloud a').handleInfo('#tagshint');

  $('input[@name="type"]').handleInfo('#typehint', 'Type');
  $('input[@name="release"]').handleInfo('#releasehint', 'Compatibility');

  // Focus first error control. If none, focus #name.
  var fields = $('input[@class="error"]:first, textarea[@class="error"]:first');
  if (fields.size()) {
    $(fields[0]).focus();
  }

  $('#tags').keyup(highlight_tags);
  $('#tags').change(highlight_tags);

  $('#cloud a').click(function() {
  var a = this;
  var tag = $(this).text();

    $('#tags').each(function() {
      if (-1 == this.value.search(tag)) {
        $(a).css('background-color', 'yellow');
        this.value = clean_tags(this.value + ' ' + tag);
      } else {
        $(a).css('background-color', 'transparent');
        this.value = clean_tags(this.value.replace(tag, ''));
      }
      $(this).focus();
    });
    return false;
  });


  highlight_tags();

});

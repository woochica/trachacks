/* Licenced under same of FieldTooltip Plugin */

jQuery(document).ready(function() {
  jQuery('th[title][rel], label[title][rel]').each(function() {
    $(this).removeAttr('title').tooltip({
      relative: "true",
      effect: "fade",
      position: "north center",
      predelay: 1000,
      tip: $(this).attr('rel')
    });
  });
});

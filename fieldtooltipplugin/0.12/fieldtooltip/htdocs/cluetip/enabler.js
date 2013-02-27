/* Licenced under same of FieldTooltip Plugin */

jQuery(document).ready(function() {
  jQuery('th[title][rel], label[title][rel]').each(function() {
    $(this).removeAttr('title');
    $(this).cluetip({
      // splitTitle: '|',
      local: true,
      sticky: true,
      closeText: '',
      mouseOutClose: 'both',
    });
  });
});

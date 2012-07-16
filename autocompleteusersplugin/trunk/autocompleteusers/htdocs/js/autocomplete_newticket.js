jQuery(document).ready(function($) {
  $("#field-owner").autocomplete("users", {
    formatItem: formatItem
  });
});
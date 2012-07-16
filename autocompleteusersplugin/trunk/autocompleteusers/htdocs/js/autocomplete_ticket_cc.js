jQuery(document).ready(function($) {
  $("#field-cc").autocomplete("../users", {
    multiple: true,
    formatItem: formatItem
  });
});
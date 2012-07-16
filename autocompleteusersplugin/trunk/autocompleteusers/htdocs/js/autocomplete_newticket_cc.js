jQuery(document).ready(function($) {
  $("#field-cc").autocomplete("subjects", {
    multiple: true,
    formatItem: formatItem,
    delay: 100
  });
});
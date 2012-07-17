$(document).ready(function() {
  function addAutocompleteBehavior() {
    $("table tr td input:text[name$='owner']").autocomplete("subjects", {
      formatItem: formatItem
    });
    $("table tr td input:text[name$='reporter']").autocomplete("subjects", {
      formatItem: formatItem
    });
    $("table tr td input:text[name$='cc']").autocomplete("subjects", {
      formatItem: formatItem
    });
  }
  addAutocompleteBehavior();
});
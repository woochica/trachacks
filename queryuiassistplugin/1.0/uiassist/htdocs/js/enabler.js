(function($) {
  // flip checkboxes named same as event source's id
  function flip(event) {
    field = this.id.slice(6)
    $('input[name="' + field + '"]').each(function() {
      checked = $(this).attr("checked")
      $(this).attr("checked", !checked)
    })
  }

  // enable only clicked checkbox and clear others
  function selectone(event) {
    that = (this.tagName == 'LABEL' ) ? $('#' + $(this).attr('for'))[0] : this;
    $('input[name="' + that.name + '"]').attr('checked', false);
    $(that).attr('checked', 'checked');
  }

  // bind "selectone" above to checkboxes in page,
  // bind "flip" above to labels in page.
  // note: clear-and-bind to avoid double-bind.
  function binder() {
    checkboxes = $("#filters input[type='checkbox']");
    for (i in checkboxes) {
      $('#label_' + checkboxes[i].name).unbind('dblclick', flip).dblclick(flip)
    }
    checkboxes.dblclick(selectone);
    $("label[for^='_0']").dblclick(selectone);
    $("label[for^='0']").dblclick(selectone);
  };
  $(document).ready(function() {
    // On Ready
    binder();
    // On Change
    setTimeout(function() {
      $("#filters select[name^=add_filter_]").change(binder)
    }, 1000);
  })
})(jQuery);
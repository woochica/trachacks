(function($) {
  // event source であるラベル の  id と一致するチェックボックスの状態を反転する
  function flip(event) {
    field = this.id.slice(6)
    $('input[name="' + field + '"]').each(function() {
      checked = $(this).attr("checked")
      $(this).attr("checked", !checked)
    })
  }

  // event source であるチェックボックスと同名のチェックボックスをすべてクリアし、sourceだけをチェックする
  function selectone(event) {
    that = (this.tagName == 'LABEL' ) ? $('#' + $(this).attr('for'))[0] : this;
    $('input[name="' + that.name + '"]').attr('checked', false);
    $(that).attr('checked', 'checked');
  }

  // ページ内にある検索条件のチェックボックスにselectoneを、それらを束ねるラベルに flip をバインドする。
  // すでにflipがバインドされている可能性があるので、一度外してみてから再バインドする。
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

// orgonchange = $($("#filters select[name^=add_filter_]")[0]).data('events')['change'][0].handler;
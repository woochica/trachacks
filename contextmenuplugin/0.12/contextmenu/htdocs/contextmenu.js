jQuery(function($) {
  $('div.context-menu').live('click', function(e) {
    var holder = $(this)
    var menu = $('div:first', holder)
    if (menu.is(':visible')) {
      menu.slideUp('fast')
    } else {
      $('div.context-menu div.ctx-foldable').hide()
      var row = holder.closest('tr')
      var top = row.position().top + row.outerHeight() - 1
      var left = (holder.position().left + holder.outerWidth()) - menu.innerWidth()
      menu.css('top', top)
          .css('left', left)
          .css('background-color', row.css('background-color')).slideDown('fast')
    }
  })
})

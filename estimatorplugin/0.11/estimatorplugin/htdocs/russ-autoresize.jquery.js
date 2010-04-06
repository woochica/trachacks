/*
 * jQuery autoResize (textarea auto-resizer)
 * @copyright russ@acceleration.net
 * @version 1.0
 */
(function($){
    $.fn.autoResize = function(options) {
        var settings = $.extend({ extraSpace : 20 }, options);
        // Only textarea's auto-resize:
        this.filter('textarea').each(function(){
	    // Get rid of scrollbars and disable WebKit resizing:
            var textarea = $(this).css({resize:'none','overflow-y':'hidden'}),
	      origHeight = textarea.height(),
	      lastScrollTop = null,
	      updateSize = function() {
		var ta = $(this);
		ta.scrollTop(10000).height(Math.max(origHeight,ta.height()+ta.scrollTop()));
              };
            // Bind namespaced handlers to appropriate events:
            textarea
                .unbind('.dynSiz')
                .bind('keyup.dynSiz', updateSize)
                .bind('keydown.dynSiz', updateSize)
                .bind('change.dynSiz', updateSize);
        });
        return this;};})(jQuery);
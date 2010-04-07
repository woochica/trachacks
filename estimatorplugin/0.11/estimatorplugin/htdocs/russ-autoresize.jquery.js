/*
 * jQuery autoResize (textarea auto-resizer)
 * @copyright russ@acceleration.net
 * @version 1.0
 */
(function($){
    $.fn.autoResize = function(options) {
        var settings = $.extend({ extraSpace : 20 }, options);
        //A textarea to play with the broweser rendering to determine height, without showing anything
	// freakin the hell out
        var testarea=$('<textarea style="position:absolute;top:-1000px;"></textarea>');
        $(document.body).append(testarea);
        // Only textarea's auto-resize:
        this.filter('textarea').each(function(){
	    // Get rid of scrollbars and disable WebKit resizing:
            var textarea = $(this).css({resize:'none','overflow-y':'hidden'}),
	      origHeight = null,
	      lastScrollTop = null,
	      updateSize = function() {
		var ta = $(this);
		if(!origHeight) origHeight = textarea.height();
		testarea.height(origHeight).val(ta.val()).scrollTop(10000);
		var newheight = testarea.height()+testarea.scrollTop();
		console.log(origHeight, newheight);
		ta.height(newheight);
              };
            // Bind namespaced handlers to appropriate events:
            textarea
                .unbind('.dynSiz')
                .bind('keyup.dynSiz', updateSize)
                .bind('keydown.dynSiz', updateSize)
                .bind('change.dynSiz', updateSize);
        });
        return this;};})(jQuery);
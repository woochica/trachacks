/*

Based on drag-and-drop sample code by Luke Dingle

http://www.lukedingle.com/javascript/sortable-table-rows-with-jquery-draggable-rows/

(C) Stepan Riha, 2009
*/
  

jQuery(document).ready(function ($) {

	// Workaround for issue when using jQuery UI < 1.8.22 with jQuery 1.8
	// Trac 1.1.1dev @r11479 provides jQuery UI 1.8.21 and jQuery 1.8.2
	// http://bugs.jquery.com/ticket/11921
	if(!$.isFunction($.fn.curCSS))
		$.curCSS = $.css;
	
	var mouseY, lastY = 0;
	
	//IE Doesn't stop selecting text when mousedown returns false we need to check
	// That onselectstart exists and return false if it does
	var hasOnSelectStart = typeof $(document).attr('onselectstart') != 'undefined';

	// Indicates whether we're dragging a row	
	var dragging = false;
	
	// This keep track of current vertical coordinates
	$().mousemove(function(e) {
		mouseY = e.pageY;
	});
	
	// Suppress behavior on elements that should capture mouse
	$('#enumlist input, #enumlist a, #enumlist select').mousedown(function (e) {
		// Suppress drag behavior for controls and links
		if(!dragging)
			mouseY = 0;
	});

	// Begin drag
	$('#enumlist tbody tr').mousedown(function (e) {
		// Suppress drag on elements that should capture mouse
	 	if(mouseY == 0)
	 		return;
	 	
	 	dragging = true;
	 	
	 	// Remember starting mouseY
		lastY = mouseY;
	
		var tr = $(this);
	
		// This is just for flashiness. It fades the TR element out to an opacity of 0.2 while it is being moved.
		tr.find('td').fadeTo('fast', 0.2);
		
		// jQuery has a fantastic function called mouseenter() which fires when the mouse enters
		// This code fires a function each time the mouse enters over any TR inside the tbody -- except $(this) one
		$('tr', tr.parent() ).not(tr).bind('mouseenter', function(e){
			// Move row based on direction
			if (mouseY > lastY) {
				$(this).after(tr);
				// Store the current location of the mouse for next time a mouseenter event triggers
				lastY = e.pageY + 1;
			} else {
				$(this).before(tr);
				// Store the current location of the mouse for next time a mouseenter event triggers
				lastY = e.pageY - 1;
			}
		});
	
		// When mouse is released, unhook events and update values
		$('body').mouseup(function () {
			//Fade the TR element back to full opacity
			tr.find('td').fadeTo('fast', 1);
			// Remove the mouseenter events from the tbody so that the TR element stops being moved
			$('tr', tr.parent()).unbind('mouseenter');
			// Remove this mouseup function until next time
			$('body').unbind('mouseup');
	
			// Make text selectable for IE again with
			// The workaround for IE based browers
			if (hasOnSelectStart)
				$(document).unbind('selectstart');
			
			updateValues(tr);
						
			dragging = false;
		});
	
	
		
	// Preventing the default action and returning false will Stop any text in the table from being
	// highlighted (this can cause problems when dragging elements)
		
	e.preventDefault();
	
	// The workaround for IE based browers
	if (hasOnSelectStart)
			$(document).bind('selectstart', function () { return false; });
		return false;
	
	}).css('cursor', 'move');
	
	// When user changes a select value, reorder rows	
	$('#enumlist select').change(function (e) {
		// Move ($this) in the right position
		var tr = $(this).parents('tr')[0];
		var val = $(this).val();
		if(val == 1) {
			$('#enumlist tbody').prepend(tr);
		} else {
			var rowIndex = 0;
			var sib = tr.previousSibling;
			while(sib != null) { rowIndex++; sib = sib.previousSibling; }
			var newIndex = val > rowIndex ? val - 1 : val - 2;
			var trBefore = $($('#enumlist tbody tr')[newIndex]);
			trBefore.after(tr);
		}
		updateValues(tr);
	});
	
	// Set select values based on the row they're in and highlight those that have changed
	function updateValues (tr) {
		var position = 1;
		var trSelect = $('select', $(tr))[0];
		$('#enumlist tbody tr select').each(function () {
			var select = $(this);
			if(select.val() != position) {
				select.val(position);
				select.not(trSelect).parent().effect('highlight', {}, 1000);
			}
			position += 1;
		});

		$(tr).effect('highlight', { }, 2000);
	}
	
});

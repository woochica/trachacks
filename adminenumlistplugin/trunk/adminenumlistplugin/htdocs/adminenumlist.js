/*
(C) Stepan Riha, 2009; Ryan J Ollos, 2012; Jun Omae, 2012

This software is licensed as described in the file COPYING, which
you should have received as part of this distribution.
*/

jQuery(document).ready(function ($) {

    // Workaround for issue when using jQuery UI < 1.8.22 with jQuery 1.8
    // Trac 1.1.1dev @r11479 provides jQuery UI 1.8.21 and jQuery 1.8.2
    // http://bugs.jquery.com/ticket/11921
    if(!$.isFunction($.curCSS)) $.curCSS = $.css;
    // The prop function doesn't exist before jQuery 1.6
    if(!$.isFunction($.fn.prop)) $.fn.prop = $.fn.attr;

    if (window.hide_selects === undefined) hide_selects = false;

    var unsaved_changes = false;
    var $remove_checkboxes = $('#enumtable tbody input:checkbox');
    var $remove_button = $('#enumtable input[name="remove"]');
    var $apply_button = $('#enumtable input[name="apply"]');

    // Insert 'Revert changes' button after the 'Apply changes' button
    var $revert_button = $('<input type="submit" name="revert" value="Revert changes" disabled="disabled"/>').insertAfter($apply_button);

    // Disable the 'Apply changes' button until there is a change
    $apply_button.prop('disabled', true);
    $('#enumtable tbody tr input:radio').click(function() {
        $apply_button.prop('disabled', false);
        $revert_button.prop('disabled', false);
    });

    // Add a checkbox for toggling the entire column of checkboxes
    var $group_checkbox = $('#enumtable thead th.sel').html('<input type="checkbox" />').children();
    $group_checkbox.click(function() {
        $remove_checkboxes.prop('checked', this.checked);
        $remove_button.prop('disabled', !this.checked);
    });

    // Disable the 'Remove selected items' button until a checkbox is selected
    $remove_button.prop('disabled', true);
    $('#enumtable tbody input:checkbox').click(function() {
        var num_checked = $remove_checkboxes.filter(':checked').length;
        if (num_checked === $remove_checkboxes.length) {
            $group_checkbox.prop('checked', true).prop('indeterminate', false);
            $remove_button.prop('disabled', false);
        }
        else if (num_checked === 0) {
            $group_checkbox.prop('checked', false).prop('indeterminate', false);
            $remove_button.prop('disabled', true);
        }
        else {
            $group_checkbox.prop('checked', false).prop('indeterminate', true);
            $remove_button.prop('disabled', false);
        }
    });

    // Hide the select boxes if the trac.ini option is true
    if (hide_selects) {
        var order_column = -1;
        $('#enumtable td:has(select)').hide().each(function() {
            order_column = $(this).parent().children().index(this);
            return false;
        });
        if (order_column !== -1) {
            $('#enumtable thead tr').each(function() {
                $($(this).children()[order_column]).hide();
            });
        }
    }

    // Prompt with a dialog if leaving the page with unsaved changes to the list
    var supports_beforeunload = jQuery.event.special.beforeunload !== undefined;
    var beforeunload = function() {
        if (unsaved_changes)
            return "You have unsaved changes to the order of the list. Your " +
                "changes will be lost if you Leave this Page before " +
                "selecting  Apply changes."
    };
    if (supports_beforeunload) {
        $(window).bind('beforeunload', beforeunload);
    } else {
        // Workaround unsupported "beforeunload" event when jQuery < 1.4,
        // e.g. Trac 0.11.x provides jQuery 1.2.x
        window.onbeforeunload = beforeunload;
        // Avoid memory leak on IE (#10656)
        $(window).bind('unload', function() { window.onbeforeunload = null; });
    }

    // Don't prompt with a dialog if the 'Apply/Revert changes' button is pressed
    var button_pressed;
    $('#enumtable div.buttons input').click(function() {
        button_pressed = $(this).attr('name');
    })

    $('#enumtable').submit(function(){
        if (button_pressed === 'apply' || button_pressed === 'revert') {
            if (supports_beforeunload)
                $(window).unbind('beforeunload');
            else
                window.onbeforeunload = null;
        }
        if (button_pressed === 'revert') {
            // Send GET request instead of POST
            location = location;
            return false;
        }
    });

    // Initialize items as sortable
    $('#enumlist tbody').css('cursor', 'move').sortable({
        axis: 'y',
        start: function(event, ui) {
            // Set the width of header to the dragging item for each column
            // in order to fit the widths to the header columns
            var cells = ui.item.children();
            var header = $(this).parent().find('thead tr');
            if (header.length === 0)
                return;
            $(header[0]).children().each(function(idx) {
                if (idx < cells.length)
                    $(cells[idx]).css('width', $(this).width() + 'px');
            });
        },
        stop: function(event, ui) { updateValues(ui.item) }
    });
    // Prevents the event bubbling in order to be able to select the select
    // widgets in `order` column on Firefox with jQuery UI 1.6
    $('#enumlist tbody').find('input, select')
                        .bind('mousedown click', function(event) {
        event.stopPropagation();
    });

    // When user changes a select value, reorder rows
    $('#enumlist select').change(function (e) {
        // Move ($this) in the right position
        var tr = $(this).parents('tr')[0];
        // select.val() does not work on IE8 with Trac 0.11.7 (#10693)
        var val = $(':selected', this).val();
        if (val == 1) {
            $('#enumlist tbody').prepend(tr);
        } else {
            var rowIndex = 0;
            var sib = tr.previousSibling;
            while (sib != null) { rowIndex++; sib = sib.previousSibling; }
            var newIndex = val > rowIndex ? val - 1 : val - 2;
            var trBefore = $($('#enumlist tbody tr')[newIndex]);
            trBefore.after(tr);
        }
        updateValues(tr);
    });

    // Set select values based on the row they're in and highlight those that have changed
    function updateValues(tr) {
        var position = 1;
        var trSelect = $('select', $(tr));
        $('#enumlist tbody select').each(function () {
            var select = $(this);
            // select.val() does not work on IE8 with Trac 0.11.7 (#10693)
            if ($(':selected', select).val() != position) {
                select.val(position);
                select.not(trSelect).parents('tr').effect('highlight', {color: '#ffb'}, 3000);
                unsaved_changes = true;
            }
            position += 1;
        });

        $(tr).effect('highlight', {}, 3000);
        if (unsaved_changes) {
            $revert_button.prop('disabled', false);
            $apply_button.prop('disabled', false);
        }
    }
});

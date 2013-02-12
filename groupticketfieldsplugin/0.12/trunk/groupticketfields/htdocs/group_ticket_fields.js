(function($){
  $.fn.enableTicketGroupFolding = function(autofold, snap) {
    var fragId = document.location.hash;
    if (fragId && /^#ticketFieldGroup\d+$/.test(fragId))
      fragId = parseInt(fragId.substr(17));
    if (snap == undefined)
      snap = false;

    var count = 1;
    return this.each(function() {
      // Use first child <a> as a trigger, or generate a trigger from the text
      var trigger = $(this).children("a").eq(0);
      if (trigger.length == 0) {
        trigger = $("<a" + (snap? " id='ticketFieldGroup" + count + "'": "")
            + " href='#ticketFieldGroup" + count + "'></a>");
        trigger.html($(this).html());
        $(this).text("");
        $(this).append(trigger);
      }

      trigger.click(function() {
        var div = $(this.parentNode.parentNode).toggleClass("collapsed");
        return snap && !div.hasClass("collapsed");
      });
      if (autofold && (count != fragId))
        trigger.parents().eq(1).addClass("collapsed");
      count++;
    });
  }
})(jQuery);

jQuery(document).ready(function($) {
    // reorder fieldsets
    if (field_groups_order) {
        for (var i = field_groups_order.length-1; i >= 0; i--) {
            var fieldset_id = 'properties';
            
            if (field_groups_order[i] != "main") {
                fieldset_id = fieldset_id + "_" + field_groups_order[i];
            }

            $('#modify').prepend($('#' + fieldset_id));
        }
    }

    // reorder ticket fields
    for (var i = 0; i < field_groups.length; i++) {
        var group = field_groups[i];
        var fieldset_id = 'properties';
        
        if (group["name"] != "main") {
            fieldset_id = fieldset_id + "_" + group["name"];
        }
        
        // Reset group name
        var fieldset = $('#' + fieldset_id);
        if (group["label"] && group["label"] != "") {
            $('legend', fieldset).text(group["label"]);
        }

        if (group['properties']) {
            if ($.inArray('foldable', group['properties']) != -1) {
                $('legend', fieldset).enableTicketGroupFolding($.inArray('collapsed', group['properties']) != -1, true);
            }
        }
        
        // Now, gather table entries and apply them to its group table
        var table = $('#table_' + group["name"]);
        var columns = 2;

        if (group['columns']) {
            columns = group['columns'];
        }

        for (var j = 0; j < group["fields"].length; j++) {
            var field_name = group["fields"][j];
            var field_id   = "field-" + field_name;
            var col_class = "col" + ((j % columns) + 1);

            // Create new row if necessary
            if ((j % columns) == 0) {
                table.append('<tr></tr>');
            }

            var label_th = $('label[for="' + field_id + '"]').parent();    // get the <th>
            label_th.attr("class", col_class);                             // fix the column class
            $('tr:last', table).append(label_th);

            var value_td = $('td').has('#' + field_id);                     // get the <td>
            if (columns == 1) {
                value_td.attr("class", "fullrow");
            } else {
                value_td.attr("class", col_class);
            }
            $('tr:last', table).append(value_td);
        }
    }

    $('tr:empty').remove();
});
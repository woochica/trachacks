var condfields = $condfields.types;
var field_types = $condfields.field_types;
var required_fields = $condfields.required_fields;

jQuery(document).ready(function ($) {
  var mode = '$condfields.mode';
  var all_fields = [];
  $('#properties tbody').find('label[for]').each(function (i, e) {
    var field = e.getAttribute('for') ? e.getAttribute('for').substr(6) : e.getAttribute('htmlFor').substr(6);
    all_fields.push(field)
  });
  var field_data = {};
  for (var i = 0; i < all_fields.length; i++) {
    var field = all_fields[i];
    field_data[field] = {
      label: $('label[for="field-' + field + '"]').parents('th'),
      input: $('#field-' + field).parents('td')
    }
  }
  //console.info(field_data);
  //console.info(mode);

  function set_type(t) {

    var condfields_fragement = $("<div/>");
    $('#properties tbody tr').each(function (i, e) {
      var lf = $(this).find("label[for]").attr('for');
      if (lf && lf.length > 6 && required_fields.join(' ').indexOf(lf.substr(6)) == -1) {
        $(this).appendTo(condfields_fragement);
      }
    })

    var col = 1;
    var rows = [];
    for (var i = 0; i < all_fields.length; i++) {
      var field = all_fields[i];
      if (!field_data[field] || field_data[field].label == null) continue;
      if (mode == 'view' && field == 'owner') continue;
      if (required_fields.join(' ').indexOf(field) != -1 || condfields[t][field] == 0) continue;

      full_row = field_types[field] == 'textarea'

      if (col == 1 || full_row) {
        var tr = $("<tr/>");
        field_data[field].label.removeClass("col2");
        field_data[field].label.addClass("col1");
        tr.append(field_data[field].label);
        field_data[field].input.removeClass("col2");
        field_data[field].input.addClass("col1");
        tr.append(field_data[field].input);
        rows.push(tr);
        col = 2;
      } else {
        tr = rows[rows.length - 1];
        field_data[field].label.removeClass("col1");
        field_data[field].label.addClass("col2");
        tr.append(field_data[field].label);
        field_data[field].input.removeClass("col1");
        field_data[field].input.addClass("col2");
        tr.append(field_data[field].input);
        col = 1;
      }

      if (full_row) {
        col = 1
      }
    }

    if (col == 2) {
      tr = rows[rows.length - 1];
      tr.append('<th class="col2"/><td class="col2"/>');
    }
    for (var i = 0; i < rows.length; i++) {
      $('#properties tbody').append(rows[i]);
    }
  }

  function set_header_type(t) {
    var elms = [
      []
    ];
    $('table.properties tr').each(function () {
      $(this).children().each(function () {
        var attr = {TH: 'id', TD: 'headers'}[this.nodeName];
        if ($(this).attr(attr) != null && condfields[t][$(this).attr(attr).substring(2)] == 1) {
          elms[0].push(this);
          if (elms[0].length == 4) {
            var tmp = $('<tr></tr>');
            $.each(elms[0], function (i, e) {
              tmp.append(e);
            });
            elms[0] = tmp;
            elms.unshift([]);
          }
        }
      });
    });
    if (elms[0].length == 0) {
      elms.shift();
    } else {
      var tmp = $('<tr></tr>');
      $.each(elms[0], function (i, e) {
        tmp.append(e);
      });
      elms[0] = tmp;
    }
    elms.reverse();
    $('table.properties').empty();
    $.each(elms, function (i, row) {
      $('table.properties').append(row);
    });
  }

  if (mode == 'view') {
    var status_re = /\(\w+ ([^:]+)(: \w+)?\)/;
    var re_results = status_re.exec($('span.status').text());
    set_header_type(re_results[1]);
  }

  set_type($('#field-type').val());

  $('#field-type').change(function () {
    set_type($(this).val());
  })
});

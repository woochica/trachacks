// load google visualization api
document.write('<script type="text/javascript" src="https://www.google.com/jsapi"></script>');
document.write('<script type="text/javascript">' +
               "  google.load('visualization', '1.0', {'packages':['corechart']});" +
               "  google.setOnLoadCallback(loaded);" +
               '</script>');

// let template know when google libs are loaded
var libs_loaded = false;
var loaded = function(){
    libs_loaded = true;
}

// populate data with data from provided table
var populate = function(data, table){
    // loop through column headers
    var columns = [];
    table.find('thead th').each(function(i,e){
        var th = jQuery(e);
        var a = th.find('a');
        if (a.length)
            var label = jQuery.trim(a.text());
        else
            var label = jQuery.trim(th.text());
        columns.push(label);
    });
    
    // loop through rows
    table.find('tbody tr:has(td)').each(function(i,e){
        var tr = jQuery(e);
        var row = [];
        var goodrow = true;

        // loop throught he cells of each row
        tr.find('td').each(function(j,e){
            var td = jQuery(e);
            // find the value
            var a = td.find('a');
            if (a.length)
              var raw = jQuery.trim(a.text());
            else
              var raw = jQuery.trim(td.text());
            
            // use hueristics to determine the data type
            var value = null;
            var type = null;
            
            // check date first
            var ms = Date.parse(raw); // no worky for safari :(
            if (isNaN(ms)) {
                // fallback to strict match on YYYY-MM-DD (or YYYY/MM/DD) format
                var match = /([0-9]{4,4})[-\/]([0-9]{2,2})[-\/]([0-9]{2,2})/.exec(raw);
                if (match) {
                    var year = parseInt(match[1]);
                    var month = parseInt(match[2]) - 1;
                    var day = parseInt(match[3]);
                    ms = new Date(year, month, day).getTime();
                }
            }
            if (!isNaN(ms) && /[-\/]/.test(raw)){
                // adjust for client-side timezone
                value = new Date(ms + new Date().getTimezoneOffset()*60000);
                type = 'date';
            } else {
                // not a date, check for a number
                value = parseFloat(raw);
                type = 'number';
                if (isNaN(value)) {
                    // not a number, assume a string
                    value = raw;
                    type = 'string';
                }
            }
            
            // if first row, add the columns
            if (i==0)
                data.addColumn(type, columns[j]);
            else if (type != data.getColumnType(j))
                goodrow = false;
            row.push(value);
        });
        if (goodrow)
            data.addRow(row);
    });
}

var get_div = function(table){
    table.before('<div id="viz"/>');
    return jQuery('#viz').get(0);
}

// analyze UX
var get_analyze = function(report){
    jQuery.ajax({
        'type': "GET",
        'url': get_url()+'/analyzeajax/list',
        'data': {'report':report},
        'success': function(analyses){
            ask_analyze(analyses);
        },
        'error': function(r,status){
            alert("Error detected:\n\n"+r.responseText);
            window.location.reload();
        }
    });
}

var ask_analyze = function(analyses){
    var id = "ask-analysis";
    if (!jQuery('#'+id).length) {
        var form = '<div id="'+id+'" title="Analyze">'
                 + '  <p>Select an analysis:</p>'
                 + '  <form>'
                 + '    <fieldset>';
        for (var i=0; i!=analyses.length; i++){
            var analysis = analyses[i];
            form +='       <input type="radio" name="analysis" id="'+analysis.path+'" value="'+analysis.num+'">'+analysis.title+'</input><br/>';
        }
            form +='       <input type="radio" name="analysis" id="all" value="0" checked="checked">All (until an issue is fixed)</input>'
                 + '    </fieldset>'
                 + '  </form>'
                 + '</div>';
        jQuery('#main').append(form);
    }
    
    jQuery('#'+id).dialog({
        autoOpen: true,
        height: 300,
        width: 400,
        modal: true,
        buttons: {
            Ok: function() {
                // extract which analysis to perform
                var selection = jQuery('#'+id+' input:radio[name=analysis]:checked');
                var num = parseInt(selection.val());
                var path = selection.attr('id');
                var next = [];
                
                // check for all analyses
                if (path == 'all'){
                    jQuery('#'+id+' input:radio[name=analysis][id!=all]').each(function(i,e){
                        var analysis = new Object();
                        analysis.num = parseInt(jQuery(e).val());
                        analysis.path = jQuery(e).attr('id');
                        next.push(analysis);
                    });
                    
                    next.reverse(); // unshift() not available in IE
                    analysis = next.pop();
                    num = analysis.num;
                    path = analysis.path;
                }
                
                jQuery(this).dialog("destroy");
                collect_rows(0, num, path, next, '');
            },
            Cancel: function() {
                jQuery(this).dialog("destroy");
            }
        },
        close: function() {
            jQuery(this).dialog("destroy");
        }
    });
    jQuery('.ui-dialog :button:first').focus();
}

// rows shizzle
var collect_rows = function(index, num, path, next, refresh){
    var rows = get_rows(index, num);
    if (rows == -1) // bogus row found so skip
        collect_rows(index+1, num, path, next, refresh);
    else if (rows)  // good rows so check em!
        check_rows(rows, path, next, refresh);
    else
        if (refresh.length) {
            jQuery('#analyzebutton').get(0).scrollIntoView(false);
            var this_report = get_report();
            var next_report = get_report(refresh);
            if (next_report == this_report)
                var which = "this report";
            else
                var which = "report "+next_report;
            var box = '<div id="refresh" title="Done!">'
                    + '  <p>Refreshing '+which+' in case fixes changed results..</p>'
                    + '</div>';
            jQuery('#main').append(box);
            jQuery('#refresh').dialog({
                autoOpen:true,
                modal:true,
                height:160,
                width:400,
                buttons: {
                    OK:function(){
                        if (next_report != this_report)
                            window.open(get_url()+'/report/'+refresh,"analyze");
                        window.location.reload();
                    }
                },
                close: function(){
                    jQuery(this).dialog("destroy");
                    jQuery('#refresh').remove();
                }
            });
        } else if (next.length) {
            var analysis = next.pop();
            collect_rows(0, analysis.num, analysis.path, next, '');
        } else {
            jQuery('#analyzebutton').get(0).scrollIntoView(false);
            var box = '<div id="done" title="Done!">'
                    + '  <p>No fixes made.</p>'
                    + '</div>';
            jQuery('#main').append(box);
            jQuery('#done').dialog({
                autoOpen:true,
                modal:true,
                height:160,
                width:300,
                buttons: {
                      OK: function(){
                        jQuery(this).dialog("destroy");
                        jQuery('#done').remove();
                    }
                },
                close: function(){
                    jQuery(this).dialog("destroy");
                    jQuery('#refresh').remove();
                }
            });
        }
}

var check_rows = function(rows, path, next, refresh){
    color_rows(rows, 'yellow');
    jQuery.ajax({
        'type': "GET",
        'url': get_url()+'/analyzeajax/'+path,
        'data': get_params(rows),
        'success': function(issue){
            if (issue.exists) 
                ask_issue(rows, path, next, refresh, issue);
            else {
                color_rows(rows);
                collect_rows(rows[0].index+1, rows.length, path, next, refresh);
            }
        },
        'error': function(r,status){
            color_rows(rows, 'red');
            alert("Error detected:\n\n"+r.responseText);
            window.location.reload();
        }
    });
}

var get_rows = function(index, num){
    var rows = new Array(num);
    for (var i=0; i!=num; i++){
        rows[i] = get_row(index+i);
        if (rows[i] == null)
            return null;
        else if (rows[i] == -1)
            return -1;
    }
    return rows;
}

var color_rows = function(rows, color, duration){
    for (var i=0; i!=rows.length; i++){
        var tr = get_tr(rows[i].index);
        if (color == null) 
            tr.css('backgroundColor', rows[i].color);
        else if (duration == null) {
            tr.css('backgroundColor', color);
            tr.get(0).scrollIntoView(false);
        }
        else {
            var row = rows[i];
            tr.css('backgroundColor', row.color);
            tr.show("highlight", {color:color}, duration, function(){
                tr.css('backgroundColor', row.color);
            });
        }
    }
}

var get_row = function(index){
    var row = new Object();
    var tr = get_tr(index);
    if (!tr.length)
        return null;
    
    // get the ticket id (assumes has class of ticket)
    row.id = parseInt(tr.find('td.ticket').text().replace(/[^\d]/g,''));
    if (isNaN(row.id))
        return -1;
    
    // get indexes (overall and in group)
    row.index = index;
    row.group_index = tr.prevAll().length;
    
    // get field name and value of first column (may help some analyses)
    var col1 = tr.find('td:first');
    row.col1_field = col1.attr('class');
    row.col1_value = jQuery.trim(col1.text());
    
    // cache row's background color
    row.color = tr.css('backgroundColor');
    
    return row;
}


// issue UX
var ask_issue = function(rows, path, next, refresh, issue){
    var id = "ask-issue";
    var form = '<div id="'+id+'" title="'+issue.title+'">'
             + '  <p>Issue: <strong>'+issue.label+'</strong></p>'
             + '  <p>Select a solution:</p>'
             + '  <form>'
             + '    <fieldset>';
    for (var i=0; i!=issue.solutions.length; i++){
        if (issue.solutions[i].disabled)
            form +='      <input type="radio" name="solution" value="'+i+'" disabled="disabled" /><span class="disabled">'+issue.solutions[i].name+' <em>(not permitted)</em></span><br/>'
        else
            form +='      <input type="radio" name="solution" value="'+i+'" /><span>'+issue.solutions[i].name+'</span><br/>'
    }
        form +='      <input type="radio" name="solution" value="-1" checked="checked">Skip this issue</input>'
             + '    </fieldset>'
             + '  </form>'
             + '</div>';
    jQuery('#main').append(form);
    
    jQuery('#'+id).dialog({
        autoOpen: true,
        height: 300,
        width: 650,
        modal: true,
        buttons: {
            Ok: function() {
                // extract which analysis to perform
                var selection = jQuery('#'+id+' input:radio[name=solution]:checked');
                var i = parseInt(selection.val());
                jQuery(this).dialog("destroy");
                jQuery('#'+id).remove();
                if (i == -1) {
                    color_rows(rows);
                    collect_rows(rows[0].index + 1, rows.length, path, next, refresh);
                }
                else {
                    refresh = refresh || issue.refresh;
                    fix_issue(rows, path, next, issue.solutions[i].data, refresh);
                }
            },
            Cancel: function() {
                jQuery(this).dialog("destroy");
                jQuery('#'+id).remove();
                color_rows(rows);
            }
        },
        close: function() {
            jQuery(this).dialog("destroy");
            jQuery('#'+id).remove();
            color_rows(rows);
        }
    });
    jQuery('.ui-dialog :button:first').focus();
}

var fix_issue = function(rows, path, next, data, refresh){
    jQuery.ajax({
        'type': "GET",
        'url': get_url()+'/analyzeajax/'+path+'/fix',
        'data': {'data': data},
        'success': function(){
            color_rows(rows, 'green', 1000);
            collect_rows(rows[0].index+rows.length, rows.length, path, next, refresh);
        },
        'error': function(r,status){
            color_rows(rows, 'red');
            alert("Error detected:\n\n"+r.responseText);
            window.location.reload();
        }
    });
}


// utils
var get_tr = function(index){
    return jQuery('table.listing.tickets tbody tr:has(td):eq('+index+')');
}

var get_url = function(){
    return jQuery('link[rel="search"]').attr('href').replace(/\/search/, '');
}

var get_report = function(text, include_params){
    if (text) 
        return text.match(/^[1-9][0-9]*/);
    else {
        if (include_params)
            var re = /\/report\/(.*)/;
        else
            var re = /\/report\/([1-9][0-9]*)/;
        var url = window.location.toString().match(re)[1];
        return url;
    }
}

var get_params = function(rows){
    var params = [];
    for (var i=0; i!=rows.length; i++){
        var param = jQuery.param(rows[i]).replace(/=/g,(i+1)+'='); // FIXME: will be wrong when there's an = inside a value
        params.push(param);
    }
    return params.join('&');
}

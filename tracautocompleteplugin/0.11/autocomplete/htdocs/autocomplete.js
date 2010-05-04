$(document).ready(function() {

    function formatItem(row, i, max) {
        return row[1] + "[" + row[0] + "]";
    }

    function formatItemSpace(row, i, max) {
        return row[0];
    }

    function formatMatch(row, i, max) {
        return row[1] + " " + row[0];
    }

    function formatResult(row) {
        return row[0];
    }

    var options = {
            max:1500,
            delay:10,
            minChars:2,
            matchSubset:0,
            matchContains:1,
            cacheLength:1,
            autoFill: false,
            scroll: true,
            scrollHeight: 300,
            formatItem: formatItem,
            formatMatch: formatMatch,
            formatResult: formatResult
        }

    var options_multi = {
            max:1500,
            delay:10,
            minChars:2,
            matchSubset:1,
            matchContains:1,
            cacheLength:1,
            autoFill: false,
            multiple: true,
            scroll: true,
            scrollHeight: 300,
            formatItem: formatItem,
            formatMatch: formatMatch,
            formatResult: formatResult
        }

    if (location.pathname.match(/newticket$/g)){
        var url_user = "ac_query/user";

        $("input[id='field-owner'],input[id='field-reporter'],input[id='field-bug_owner']").autocomplete(url_user, options);

        $("input[id='field-cc']").autocomplete(url_user, options_multi);
        
    } else{
        var url_user = "../ac_query/user";
        
        $("input[id='field-owner'],input[id='field-bug_owner'],input[id='field-reporter'],input[id='field-author'],input[id='assign_reassign_owner'],input[id='action_reassign_reassign_owner']").autocomplete(url_user, options);
        $("input[id='field-cc']").autocomplete(url_user, options_multi);
        
    }
    
    var dialog_html = 
'<div class="ui-dialog-content ui-widget-content" id="edit_cc_dialog">' +
'    <div style="width: 260px; height: 40px; font-size: 12px;"></div>' +
'    <div style="width: 260px; height: 40px;">' +
'       <table style="width: 90%;">' +
'        <tr>' +
'            <td>' +
'            <input type="text" id="input_new_cc"/>' +
'            </td>' +
'            <td style="width: 80px;">' +
'            <input type="button" id="add_new_cc" value="Add" />' +
'            </td>' +
'        </tr>' +
'    </table>' +
'    </div>' +
'    <div style="width: 260px; height: 300px; overflow:auto;">' +
'       <table id="edit_cc_content" style="width: 90%;">' +
'       </table>' +
'    </div>' +
'</div>';

    var prepend = function(cc){
        var cc = $.trim(cc);
        if (!cc){
            return;
        }
        
        var ccs = [];
        $("#edit_cc_content input[name='list_cc']").each(function(){
            ccs.push($(this).val());
        });
        
        
        for (var i=0; i<ccs.length; i++){
            if ($.trim(ccs[i]) == cc){
                $("#edit_cc_content input[name='list_cc']").each(function(){
                    if ($.trim($(this).val()) == cc) {
                        $(this).fadeOut().fadeIn("slow");
                    }
                });
                return;
            }
        }
        
        var cc_tr = $('<tr><td><input type="text" name="list_cc" value="'+cc+'"/></td><td style="width: 80px;"><input type="button" value="Del" class="delete_cc"></td></tr>');
        $("input.delete_cc", cc_tr).click(function(){
            $(this).parent().parent().remove();
        });
        
        $("#edit_cc_content").prepend(cc_tr);
        
        $("input[name='list_cc']").autocomplete(url_user, options);
    };
    
    $("#field-cc").after('<a id="edit_cc" title="" href="#">Edit</a>');
    
    $("#edit_cc").click(function(){
        $("#footer").append(dialog_html);
        
        $("input[id='input_new_cc']").autocomplete(url_user, options);
        
        $("#add_new_cc").click(function(){
            var input_new_cc = $.trim($("#input_new_cc").val());
            if (!input_new_cc){
                return;
            }
            
            prepend(input_new_cc);
            
            $("#input_new_cc").val("").focus();
            
        });
        
        $("#input_new_cc").change(function(){
            $("#add_new_cc").click();
        });
        
        $("#edit_cc_dialog").dialog({ 
            buttons: { "Close": function() { $(this).dialog("close"); } },
            stackfix: true,
            height: 540,
            modal: true,
            resizable: false,
            draggable: false,
            title: 'Edit cc',
            zIndex: 3999,
            open: function(event, ui) {
                var ccs = $.trim($("#field-cc").val()).split(",");
                
                for (var i=0; i<ccs.length; i++){
                    prepend(ccs[i]);
                }
            },
            close: function(event, ui) {
                var ccs = [];
                $("#edit_cc_content input[name='list_cc']").each(function(){
                    ccs.push($(this).val());
                });
                ccs.reverse();
                
                $("#field-cc").val(ccs.join(", "));
                
                $("#edit_cc_dialog").remove();
            },
            bgiframe: true 
        });
        return false;
    });
    



});



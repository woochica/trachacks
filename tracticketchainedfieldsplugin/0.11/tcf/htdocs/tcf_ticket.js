$(document).ready(function() {
    
    function handleTcfQuery(result) {
        if (result == 0 || result == -1) {
            return;
        }
        var tcf_define = result["tcf_define"];
        var chained_fields = result["chained_fields"];
        if (chained_fields.length) {
            var selector_inputs = [];
            var selector_selects = [];
            for (var i=0; i<chained_fields.length; i++ ) {
                var field = chained_fields[i];
                selector_inputs.push("input#field-" + field);
                selector_selects.push("select#field-" + field);
            }
            var field_selector_input = selector_inputs.join(",");
            var field_selector_select = selector_selects.join(",");
            
        } else {
            var field_selector_input = "input[id^='field-tcf_']";
            var field_selector_select = "select[id^='field-tcf_']";
        }
        
        var tcf_orig_values = {};
        
        $(field_selector_input).each(function(){
            var new_field = $('<select name="'+$(this).attr("name")+'"/>');
            var id = this.id;
            
            tcf_orig_values[id] = $(this).val();
            
            $(this).after(new_field);
            
            $(this).remove();
            
            new_field.attr("id", id);
        });
        
        $(field_selector_select).change(function(){
            if (location.pathname.match(/newticket/g)){
                var url = "tcf/query_field_change";
            } else{
                var url = "../tcf/query_field_change";
            }
            
            var data = {"trigger": this.id};
        
            $(field_selector_select).each(function(){
                data[this.id] = $(this).val();
            });
            
            var responseText = $.ajax({
                url: url,
                data: data,
                cache: false,
                dataType: 'json',
                async: false
            }).responseText;
        
            try {
                var result = eval("(" + responseText + ")");
            } catch (e) {
                alert("Failed to parse result from server.");
            }
            
            if (result.status != "1"){
                alert("Error occurs.");
            }
            
            for (var j=0; j<result.targets.length; j++) {
                var target = result.targets[j];
                var target_field = target["target_field"];
                var target_options = target["target_options"];
                
                $("#field-" + target_field).empty();
                for (var i=0; i<target_options.length; i++){
                    var field_option = target_options[i];
                    $("#field-" + target_field).append("<option>"+field_option+"</option>");
                }
                $("#field-" + target_field).append("<option></option>");
                
                if (result.hide_empty_fields && 
                    (target_options.length == 0 && target_field || 
                    $(this).css("display") == "none")
                   ){
                    $("#field-"+target_field).parent().prev().find("label").hide();
                    $("#field-"+target_field).hide();
                } else {
                    $("#field-"+target_field).parent().prev().find("label").show();
                    $("#field-"+target_field).show();
                }
                
                $("#field-" + target_field).change();
            }
        });
        
        for (var field in tcf_define) {
            var orig_value = $("#field-"+field).val();

            $("#field-"+field).empty();
            
            var root_options = [];
            for (var field_option in tcf_define[field]){
                root_options.push(field_option);
            }
            
            root_options.sort(function(x,y){ 
                  var a = String(x).toUpperCase(); 
                  var b = String(y).toUpperCase(); 
                  if (a > b) 
                     return 1 
                  if (a < b) 
                     return -1 
                  return 0; 
                }); 
            
            for (var i in root_options){
                field_option = root_options[i];
                $("#field-"+field).append("<option>"+field_option+"</option>");
            }
            
            $("#field-"+field).append("<option></option>");
            
            if (location.pathname.match(/newticket/g)){
                $("#field-"+field).change();
            } else {
                $("#field-"+field).val(orig_value);
            }
        }
        
        if ($("#ticket.ticketdraft").length) {
            var preview_mode = true;
        } else {
            var preview_mode = false;
        }
        
        if (!location.pathname.match(/newticket/g) || preview_mode){
            $(field_selector_select).each(function(){
                var orig_value = tcf_orig_values[this.id];
                
                var options = {};
                $("option", $(this)).each(function(){
                    var val = $(this).val();
                    if (val) {
                        options[val] = null;
                    }
                });
                
                if (orig_value in options){
                    $(this).val(orig_value);
                    $(this).change();
                } else {
                    $(this).append("<option>"+orig_value+"</option>");
                    $(this).val(orig_value);
                    $(this).change();
                }
            });
        }
        
    }
    
    if (location.pathname.match(/newticket/g)){
        var url = "tcf/query_tcf_define";
    } else{
        var url = "../tcf/query_tcf_define";
    }
    
    $.getJSON(url, handleTcfQuery);
    
    
});

$(document).ready(function() {
    
    function handleTcfQuery(result) {
        if (result == 0 || result == -1) {
            return;
        }
        var tcf_define = result["tcf_define"];
        
        var tcf_orig_values = {};
        
        $("input[id^='field-tcf_']").each(function(){
            var new_field = $('<select name="'+$(this).attr("name")+'"/>');
            var id = this.id;
            
            tcf_orig_values[id] = $(this).val();
            
            $(this).after(new_field);
            
            $(this).remove();
            
            new_field.attr("id", id);
        });
        
        $("select[id^='field-tcf_']").change(function(){
            if (location.pathname.match(/newticket/g)){
                var url = "tcf/query_field_change";
            } else{
                var url = "../tcf/query_field_change";
            }
            
            var data = {"trigger": this.id};
        
            $("select[id^='field-tcf_']").each(function(){
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
            
            $("#field-" + result.target_field).empty();
            for (var i in result.target_options){
                var field_option = result.target_options[i];
                $("#field-" + result.target_field).append("<option>"+field_option+"</option>");
            }
            $("#field-" + result.target_field).append("<option></option>");
            
            
            if (result.hide_empty_fields && 
                (result.target_options.length == 0 && result.target_field || 
                $(this).css("display") == "none")
               ){
                $("#field-"+result.target_field).parent().prev().find("label").hide();
                $("#field-"+result.target_field).hide();
            } else {
                $("#field-"+result.target_field).parent().prev().find("label").show();
                $("#field-"+result.target_field).show();
            }
            
            $("#field-" + result.target_field).change();
            
        });
        
        for (var field in tcf_define) {
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
            }
            break;
        }
        
        
        if (!location.pathname.match(/newticket/g)){
            $("select[id^='field-tcf_']").each(function(){
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

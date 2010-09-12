/*
 * Rule 'class'
 */
var Rule = function(name){
    var noop = function(input, spec){};
    this.setup    = noop;
    this.apply    = noop;
    this.complete = noop;
    
    // register this rule by adding to global variable
    if (window.dynfields_rules == undefined)
        window.dynfields_rules = new Object();
    window.dynfields_rules[name] = this;
}


/*
 * ClearRule implementation
 */
var clearrule = new Rule('ClearRule'); // must match python class name exactly

// apply
clearrule.apply = function(input, spec){
    var target = spec.target;

    if (spec.clear_on_change == undefined)
        return;
    
    var fld = jQuery('#field-'+target);
    if (fld.hasClass('clearable')){
        fld.val('').change();
    } else {
        fld.addClass('clearable');
    }
};


/*
 * CopyRule implementation
 */
var copyrule = new Rule('CopyRule'); // must match python class name exactly

// apply
copyrule.apply = function(input, spec){
    var target = spec.target;

    if (spec.value == undefined)
        return;
        
    var fld = jQuery('#field-'+target);
    if (spec.overwrite.toLowerCase() == 'false'){
        if (fld.val() != '' || fld.is(":hidden"))
            return;
    }
    
    if (fld.hasClass('copyable')){
        // only do effect if value is changing
        var doit = true;
        if (fld.get(0).tagName.toLowerCase() == 'select'){
            var opts = new Array();
            fld.find('option').each(function(i,e){
                opts.push($(e).text());
            });
            if (jQuery.inArray(input.val(), opts) == -1){
                doit = false;
            }
        } 
        if (doit){
            fld.hide();
            fld.val(input.val()).change();
            fld.fadeIn('slow');
        }
    } else {
        fld.addClass('copyable');
    }
};


/*
 * DefaultValueRule implementation
 */
var defaultrule = new Rule('DefaultValueRule'); // must match python class name exactly

// apply
defaultrule.apply = function(input, spec){
    if (window.location.pathname.indexOf('/newticket') == -1)
        return;
    
    var fld = jQuery('#field-'+spec.target);
    if (!fld.hasClass('defaulted')){
        var doit = true;
        if (fld.get(0).tagName.toLowerCase() == 'select'){
            var opts = new Array();
            fld.find('option').each(function(i,e){
                opts.push($(e).text());
            });
            if (jQuery.inArray(spec.value, opts) == -1){
                doit = false;
            }
        } 
        if (doit){
            fld.val(spec.value).change(); // cascade rules
        }
        
        fld.addClass('defaulted');
    }
};


/*
 * HideRule implementation
 */
var hiderule = new Rule('HideRule'); // must match python class name exactly

// setup
hiderule.setup = function(input, spec){
    // show and reset elements controlled by this input field
    var trigger = input.attr('id').substring(6); // ids start with 'field-'
    jQuery('.dynfields-'+trigger)
        .removeClass('dynfields-hide dynfields-'+trigger)
        .show();
};

// apply
hiderule.apply = function(input, spec){
    var trigger = spec.trigger;
    var target = spec.target;
    
    // process hide rule
    var v = input.val();
    var l = spec.trigger_value.split('|'); // supports list of trigger values
    if ((jQuery.inArray(v,l) != -1 && spec.op == 'hide') ||
        (jQuery.inArray(v,l) == -1 && spec.op == 'show')){
        
        // we want to hide the input fields's td and related th
        var field = jQuery('#field-'+target);
        var td = field.parents('td:first');
        var th = td.siblings('th')
                   .find('label[for=field-'+target+']')
                   .parents('th:first');
        td.addClass('dynfields-hide dynfields-'+trigger);
        th.addClass('dynfields-hide dynfields-'+trigger);
            
        // let's also clear out the field's value to avoid confusion
        if (spec.clear_on_hide.toLowerCase() == 'true'){
            if (field.val().length)
                field.val('').change(); // cascade rules
                
            // assume we now also want to hide field in the header
            th = jQuery('#h_'+target);
            td = th.siblings('td[headers=h_'+target+']');
            td.addClass('dynfields-hide dynfields-'+trigger);
            th.addClass('dynfields-hide dynfields-'+trigger);
        }
    }        
};

// complete
hiderule.complete = function(input, spec){
    jQuery('.dynfields-hide').hide();
    
    // update layout (see layout.js)
    inputs_layout.update(spec);
    header_layout.update(spec);
};

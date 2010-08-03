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
        fld.val('');
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
    if (fld.val() != '' || fld.is(":hidden"))
        return;
    
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
            fld.val(input.val());
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
            fld.val(spec.value);
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
    // show and reset elements controlled by this input field and derived nodes
    var trigger = input.attr('id').substring(6); // ids start with 'field-'
    jQuery('.dynfields-'+trigger)
        .removeClass('dynfields-hide dynfields-'+trigger)
        .show();
    jQuery('.dynfields-derived')
        .removeClass('dynfields-hide dynfields-derived')
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
        var td = jQuery('#field-'+target).parents('td:first');
        var th = td.siblings('th')
                   .find('label[for=field-'+target+']')
                   .parents('th:first');
        td.addClass('dynfields-hide dynfields-'+trigger);
        th.addClass('dynfields-hide dynfields-'+trigger);
            
        // let's also clear out the field value to avoid confusion
        if (spec.clear_on_hide.toLowerCase() == 'true'){
            jQuery('#field-'+target).val('');
                
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
    // if all cells in row are marked hidden, then hide whole row, too!
    jQuery('.dynfields-hide').each(function(i){
        if (jQuery(this).siblings().size() == jQuery(this).siblings('.dynfields-hide').size()){
            jQuery(this).parents('tr:first').addClass('dynfields-hide dynfields-derived');
        };
    });
    jQuery('.dynfields-hide').hide();
};


/*
 * Rule 'class'
 */
var Rule = function(name){
    var noop = function(input, spec){};
    this.setup    = noop;
    this.apply    = noop;
    this.complete = noop;
    this.query    = function(spec){}; // for query page
    
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
    
    var field = jQuery('#field-'+target);
    if (field.hasClass('clearable')){
        // only cascade rules if value changes
        var oldval = field.val();
        var newval = field.val('').val();
        if (oldval != newval)
            field.change(); // cascade rules
    } else {
        field.addClass('clearable');
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
        
    var field = jQuery('#field-'+target);
    if (spec.overwrite.toLowerCase() == 'false' && field.val() != '')
        return;
    
    if (field.hasClass('copyable')){
        // only do effect if value is changing
        var doit = true;
        if (field.get(0).tagName.toLowerCase() == 'select'){
            var opts = new Array();
            field.find('option').each(function(i,e){
                opts.push(jQuery(e).text());
            });
            if (jQuery.inArray(input.val(), opts) == -1){
                doit = false;
            }
        }
        if (doit && field.val() != input.val()){
            field.hide();
            field.val(input.val()).change();
            field.fadeIn('slow');
        }
    } else {
        field.addClass('copyable');
    }
};


/*
 * DefaultValueRule implementation
 */
var defaultrule = new Rule('DefaultValueRule'); // must match python class name exactly

// apply
defaultrule.apply = function(input, spec){
    var field = jQuery('#field-'+spec.target);
    if (!field.hasClass('defaulted')){
        field.addClass('defaulted');
        var doit = true;
        var value = spec.value;
        
        // ensure default value is in list of select options
        if (field.get(0).tagName.toLowerCase() == 'select'){
            var opts = new Array();
            field.find('option').each(function(i,e){
                opts.push(jQuery(e).text());
            });
            if (jQuery.inArray(value, opts) == -1)
                doit = false;
        }
            
        // ensure an 'empty' option value for existing tickets (unless appending)
        if (field.val().length > 1 &&
           window.location.pathname.indexOf('/ticket') > -1){
            doit = spec.append.toLowerCase() == 'true';
            if (doit){
                // append preference to text field's value
                var values = new Array();
                jQuery(field.val().split(',')).each(function(i,v){
                    values.push(jQuery.trim(v));
                });
                // the preference value could be comma-delimited list itself
                jQuery(value.split(',')).each(function(i,v){
                    v = jQuery.trim(v);
                    if (jQuery.inArray(v, values) == -1){
                        values.push(v);
                    }
                });
                value = values.join(', ');
            }
        }
        
        if (doit)
            field.val(value).change(); // cascade rules
    }
};


/*
 * HideRule implementation
 */
var hiderule = new Rule('HideRule'); // must match python class name exactly

// setup
hiderule.setup = function(input, spec){
    var id = input.attr('id');
    if (id){ // no input fields when on /query page
        // show and reset elements controlled by this input field
        var trigger = id.substring(6); // ids start with 'field-'
        jQuery('.dynfields-'+trigger)
            .removeClass('dynfields-hide dynfields-'+trigger)
            .show();
    }
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
        var cls = 'dynfields-hide dynfields-'+trigger;
        if (spec.link_to_show.toLowerCase() == 'true')
            cls += ' dynfields-link';
        td.addClass(cls);
        th.addClass(cls);
        
        // let's also clear out the field's value to avoid confusion
        if (spec.clear_on_hide.toLowerCase() == 'true' &&
            field.val() && field.val().length){ // Chrome fix - see #8654
            if (field.attr('type') == 'checkbox'){
                if (field.is(':checked')){
                    field.removeAttr('checked').change();
                }
            } else {
                // only cascade rules if value changes
                var oldval = field.val();
                var newval = field.val('').val();
                if (oldval != newval)
                    field.change(); // cascade rules
            }
        }
        
        // hide field in the header if cleared or always hidden
        if (spec.clear_on_hide.toLowerCase() == 'true' ||
            spec.hide_always.toLowerCase() == 'true'){
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
    
    // add link to show hidden fields (that are enabled to be shown)
    if (spec.link_to_show.toLowerCase() == 'true'){
        if (jQuery('#dynfields-show-link').length == 0){
            var html = '<tr id="dynfields-show-link">' +
            '  <th></th><td></td><th></th><td>' +
            '    <a href="#no3" onClick="jQuery(\'.dynfields-link\').show(); jQuery(\'#dynfields-show-link\').remove();">Show hidden fields</a>' +
            '  </td>' +
            '</tr>';
            jQuery('.dynfields-link:last').parents('tbody:first').append(html);
        }
    }
};

// query
hiderule.query = function(spec){
    // hide hide_always fields on /query page
    if (spec.hide_always.toLowerCase() == 'true'){
        // hide from columns section
        jQuery('input[value="'+spec.target+'"]')
              .attr('checked',false)
              .parent().hide();
        // hide from and/or column filters/dropdowns
        jQuery('#add_filter option[value="'+spec.target+'"]') // trac <= 0.12.1
              .hide();
        jQuery('.actions option[value="'+spec.target+'"]') // trac 0.12.2
              .hide();
    }
};


/*
 * ValidateRule implementation
 */
var validaterule = new Rule('ValidateRule'); // must match python class name exactly

// setup
validaterule.setup = function(input, spec){
    var field = jQuery('#field-'+spec.target);
    var form = jQuery('input[name=submit]')
                .click(function(){
                    // reset "alert only once per form submission"
                    $(this).parents('form').removeClass('validated');
                 })
                .parents('form');
    
    // 'owner' field is special case 
    if (spec.target == 'owner' &&
        input.attr('id').indexOf('ssign_reassign_owner') != -1)
        field = jQuery(input);
    
    // proceed only if input field matches the spec's target field
    if (input.attr('id') == field.attr('id') && !field.hasClass('validated')){
        field.addClass('validated');
        
        // listen for form submission
        form.submit(function(){
            if (field.is(":hidden"))
                return true;
            if ((spec.value == "" && input.val() == "") ||
                (spec.value != "" && RegExp(spec.value).test(input.val()))){
                // alert only once per form submission
                if (!form.hasClass('validated')){
                    form.addClass('validated');
                    if (spec.value == '')
                        var e = 'be empty';
                    else
                        var e = 'equal '+spec.value;
                    alert(spec.target+" must not "+e);
                    field.focus();
                }
                return false;
            } else {
                return true;
            }
        });
    }
};

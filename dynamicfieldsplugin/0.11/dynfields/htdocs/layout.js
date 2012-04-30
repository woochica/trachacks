/*
 * Layout 'class'
 */
var Layout = function(name){
    this.name = name;
    
    // Selector for all field tds/ths
    this.selector = '';

    // Return the given field name's td/th element
    this.get_tx = function(field){}
    
    // Return the given td/th element's field name 
    this.get_field = function(tx){}
    
    // Move a field's tds and ths to slot i
    this.move_field = function(field, i){}
    
    // Returns true of the field needs its own row
    this.needs_own_row = function(field){
        var fld = jQuery('#field-'+field);
        if (fld.length)
            if (fld.get(0).tagName == 'TEXTAREA')
              return true;
            else
              return false;
        return false;
    }
    
    // Update the field layout given a spec
    this.update = function(spec){
        var this_ = this;
        
        // save original field order
        if (window.dynfields_orig_field_order == undefined)
            window.dynfields_orig_field_order = Object();
        
        if (window.dynfields_orig_field_order[this.name] == undefined){
            window.dynfields_orig_field_order[this.name] = [];
            jQuery(this.selector).each(function(i,e){
                var field = this_.get_field($(this));
                if (field)
                    window.dynfields_orig_field_order[this_.name].push(field);
            });
        }
        
        // get visible and hidden fields
        var visible = [];
        var hidden = [];
        jQuery.each(window.dynfields_orig_field_order[this.name], function(i,field){
            var tx = this_.get_tx(field);
            if (tx.hasClass('dynfields-hide')){
                hidden.push(field);
            } else {
                visible.push(field);
            }
        });
        
        // get new field order
        var new_fields = jQuery.merge(visible, hidden); // warning: side-effects!
        
        // order the fields
        this.order_fields(new_fields);
    }
    
    this.order_fields = function(new_fields){
        var this_ = this;
        var skip_slot = 0;
        
        // determine which fields need to move and move 'em!
        jQuery(this.selector).each(function(i,e){
            var old_field = this_.get_field($(this));
            var old_slot = -1;
            if (old_field.length)
                old_slot = jQuery.inArray(old_field, new_fields);
            var new_field = new_fields[i];
            
            // check to allow *this* field be in its own row
            if (i%2==1 && old_field.length && this_.needs_own_row(new_field))
                skip_slot += 1;
            
            var new_slot = i+skip_slot;
            
            // check if field is in the correct slot in the new order
            if (new_slot != old_slot && i < new_fields.length){
                // wrong order!
                this_.move_field(new_field, new_slot);
            }
            
            // check to move *next* field to its own row
            if (old_field.length && this_.needs_own_row(new_field))
                skip_slot += 1;
        });
    }
};


/*
 * Inputs Layout implementation
 */
var inputs_layout = new Layout('inputs');

// selector
inputs_layout.selector = '#properties td[class!=fullrow]:parent';

// get_tx
inputs_layout.get_tx = function(field){
    return jQuery('#field-'+field).parents('td:first');
};

// get_field
inputs_layout.get_field = function(td){
    var input = td.find(':input:first');
    if (!input.length) return '';
    return input.attr('id').slice(6);
};

// move_field
inputs_layout.move_field = function(field, i){
    var td = this.get_tx(field);
    var th = td.parent('tr')
               .find('th label[for=field-'+field+']')
               .parent('th');
    
    // find correct row (tr) to insert field
    var row = Math.round(i/2 - 0.5); // round down
    row += jQuery('#properties td[class=fullrow]').length; // skip fullrows
    var tr = jQuery('#properties tr:eq('+row+')');
    
    // find correct column (tx) to insert field
    var col = 'col'+((i%2)+1);
    if (tr.find('th').length){
        if (col == 'col1'){
            var old_th = tr.find('th:first');
            if (old_th.get(0) != th.get(0)){ // don't move self to self
                old_th.before(th);
                old_th.before(td);
            }
        } else {
            var old_td = tr.find('td:has(:input):last');
            if (old_td.get(0) != td.get(0)){ // don't move self to self
                old_td.after(td);
                old_td.after(th);
            }
        }
    } else {
        // no columns so just insert
        tr.append(th);
        tr.append(td);
    }
    
    // let's set col
    td.removeClass('col1 col2');
    th.removeClass('col1 col2');
    td.addClass(col);
    th.addClass(col);
};


/*
 * Header Layout implementation
 */
var header_layout = new Layout('header');

// selector
header_layout.selector = '#ticket .properties th:parent';

// get_tx
header_layout.get_tx = function(field){
    return jQuery('#h_'+field);
};

// get_field
header_layout.get_field = function(th){
    return (th.attr('id') ? th.attr('id').slice(2) : '');
};

// move_field
header_layout.move_field = function(field, i){
    var th = this.get_tx(field);
    var td = th.parent('tr').find('td[headers=h_'+field+']');
    
    // find correct row (tr) to insert field
    var row = Math.round(i/2 - 0.5); // round down
    var tr = jQuery('#ticket .properties tr:eq('+row+')');
    
    // find correct column (tx) to insert field
    if (tr.find('th').length){
        if (i % 2 == 0){
            var old_th = tr.find('th:first');
            if (old_th.get(0) != th.get(0)){ // don't move self to self
                old_th.before(th);
                old_th.before(td);
            }
        } else {
            var old_td = tr.find('td:last');
            if (old_td.get(0) != td.get(0)){ // don't move self to self
                old_td.after(td);
                old_td.after(th);
            }
        }
    } else {
        // no columns so just insert
        tr.append(th);
        tr.append(td);
    }
};

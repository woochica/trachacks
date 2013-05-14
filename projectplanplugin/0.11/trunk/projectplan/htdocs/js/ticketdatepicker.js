/**
 * beta
 * adds javascript jQuery UI date picker to ticket fields
 */

$(document).ready(function () {
  
    if (!jQuery.ui) {
      $.ajax({
	url: "http://code.jquery.com/ui/1.10.3/jquery-ui.js", // load from CDN
	dataType: "script",
	cache: true,
	success: function(){ initPPticketDatePicker(); }
      });
    } else {
      console.log("initPPticketDatePicker: jquery ui was already loaded.")
      initPPticketDatePicker();
    }
});

function initPPticketDatePicker(){
    $.datepicker.setDefaults({
      showOn: "both",
      calculateWeekType: true,
      showWeek: true,
      showAnim: "fadeIn",
      gotoCurrent: true,
      firstDay: 1,
      showButtonPanel: true,
      currentText: "current"
    }); 
    console.log("initPPticketDatePicker: init: "+($("#custom_due_assign_field_id").html())+", "+($("#custom_due_close_field_id").html()) );
    $("#field-"+$("#custom_due_assign_field_id").html()).datepicker('destroy'); // safety
    $("#field-"+$("#custom_due_assign_field_id").html()).datepicker( { dateFormat: $("#custom_due_assign_field_format").html().toLowerCase().replace("yyyy","yy") } );
    $("#field-"+$("#custom_due_close_field_id").html()).datepicker('destroy'); // safety
    $("#field-"+$("#custom_due_close_field_id").html()).datepicker( { dateFormat: $("#custom_due_close_field_format").html().toLowerCase().replace("yyyy","yy") } );
    $(".ui-datepicker-trigger").hide();
}





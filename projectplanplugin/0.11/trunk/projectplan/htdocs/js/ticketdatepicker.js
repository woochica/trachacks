/**
 * beta
 * adds javascript jQuery UI date picker to ticket fields
 */

$(document).ready(function () {
	// custom_due_assign_field_format
	// custom_due_close_field_format
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
	// $.datepicker.formatDate( "dd/mm/yyyy" );
	$("#field-"+$("#custom_due_assign_field_id").html()).datepicker( { dateFormat: $("#custom_due_assign_field_format").html().toLowerCase().replace("yyyy","yy") } );
	$("#field-"+$("#custom_due_close_field_id").html()).datepicker( { dateFormat: $("#custom_due_close_field_format").html().toLowerCase().replace("yyyy","yy") } );
	$(".ui-datepicker-trigger").hide();
});





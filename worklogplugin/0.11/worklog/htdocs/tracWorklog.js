/*
 * Work log plugin JavaScript code.
 *
 * This assumes that jQuery, jqModal and jCalendar are all loaded.
 */

var tracWorklog = {
  
  start: function() { return true; },
  stop: function() {
    var mynow = new Date();
    change_handler = function() {
      var chosen_date = $.datepicker.getDateFor('#worklogStopDate');
      var chosen_time = $.timeEntry.getTimeFor('#worklogStopTime');
      
      var chosen = new Date();
      chosen.setTime(chosen_date.getTime() + (((chosen_time.getHours() * 60) + chosen_time.getMinutes()) * 60) * 1000);
      
      var now = new Date();
      if (chosen > now)
        $('#worklogSubmit')[0].disabled = true;
      else
        $('#worklogSubmit')[0].disabled = false;
      
      $('#worklogStoptime')[0].value = (chosen.getTime() / 1000);
    };
    
    $('#worklogStopDate').datepicker({onSelect: change_handler,
                                    maxDate: new Date()});
    $('#worklogPopup').jqm({modal: true}).jqmShow();
    
    try {
    $('#worklogStopTime').timeEntry({show24Hours: true, spinnerImage: ''});
    $.timeEntry.setTimeFor('#worklogStopTime', mynow);
    $('#worklogStopTime').bind('change', change_handler);
    }
    catch (er) {
      alert(er);
    }
    return false;
  }
};

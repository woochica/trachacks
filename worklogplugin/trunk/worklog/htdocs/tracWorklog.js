/*
 * Work log plugin JavaScript code.
 *
 * This assumes that jQuery, jqModal and jCalendar are all loaded.
 */

var tracWorklog = {
  
  start: function() { return true; },
  stop: function() {
    var mynow = new Date();
    var change_handler = function()
    {
      var chosen_date = $('#worklogStopDate').datepicker('getDate');
      var chosen_time = $('#worklogStopTime').timeEntry('getTime');
      
      var chosen = new Date();
      chosen.setTime(chosen_date.getTime() + (((chosen_time.getHours() * 60) + chosen_time.getMinutes()) * 60) * 1000);
      
      $('#worklogSubmit')[0].disabled = (chosen > (new Date()));
      $('#worklogStoptime')[0].value = (chosen.getTime() / 1000);
    };
    
    $('#worklogStopDate').datepicker({onSelect: change_handler,
                                    maxDate: new Date()});
    $('#worklogPopup').jqm({modal: true}).jqmShow();
    
    try
    {
      $('#worklogStopTime').timeEntry({show24Hours: true, spinnerImage: ''});
      $('#worklogStopTime').timeEntry('setTime', mynow);
      $('#worklogStopTime').bind('change', change_handler);
    }
    catch (er) 
    {
      alert(er);
    }
    return false;
  }
};

/**
 * AnBo
 * experimental
 * ticket: adds javascript to add a button allowing to create a depending ticket
 * newticket: adds given ticket number to dependencies field
 */

/**
 * add button
 */
function ppCreateNewDependingTicket()
{
  if( /\/ticket\//.test(window.location.href) ) {
    $('.buttons').append('<input type="button" name="ppCreateNewDependingTicket" value="Create new depending ticket" onclick="ppCreateNewDependingTicketAction()">');
  }
}

/**
 * add dependencies ticket to new ticket form
 */
function ppAddDependenciesToNewDependingTicket()
{
  if( /\/newticket/.test(window.location.href) ) {
  pos = window.location.search.search(/\?dep=/);
    if( pos > -1 ) {
      $('#field-dependencies').val(window.location.search.substr(pos+('?dep='.length)));
    }
  }
}

/**
 * new form action
 */
function ppCreateNewDependingTicketAction() {
  window.location.href = window.location.href.replace(/\/ticket\//, '/newticket?dep=' );
}
 


$(document).ready(function () {
	ppCreateNewDependingTicket();
	ppAddDependenciesToNewDependingTicket();
});





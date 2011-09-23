
var modified_tickets = new Array();
var added_tickets = new Array();

function importexportxls_set_import_checkbox(checked)
{
    index = 0;
    checkbox = document.getElementById('ticket.'+index);
    while( checkbox )
    {
        checkbox.checked = checked;
        index++;
        checkbox = document.getElementById('ticket.'+index);
    }
}

function importexportxls_select(checkbox_ids)
{
    for( var checkbox_id in checkbox_ids)
    {
        document.getElementById(checkbox_id).checked = true;
    }
}


var modified_tickets = new Array();
var added_tickets = new Array();

function importexportxls_set_import_checkbox(checked)
{
    var index = 0;
    var checkbox = document.getElementById('ticket.'+index);
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

function importexportxls_hide(added_ids, modified_ids, hide)
{
    var index = 0;
    var checkbox = document.getElementById('ticket.'+index);
    while( checkbox )
    {
        if( !( 'ticket.'+index in added_ids ) && !( 'ticket.'+index in modified_ids ) )
        {
            // input -> td -> tr
            if( typeof( checkbox.parentNode.parentNode.hidden ) != 'undefined' )
            {
                checkbox.parentNode.parentNode.hidden = hide;
            }
            else
            {
                checkbox.parentNode.parentNode.style.display = ( hide ? 'none' : 'block' );
            }
        }
        index++;
        checkbox = document.getElementById('ticket.'+index);
    }
}

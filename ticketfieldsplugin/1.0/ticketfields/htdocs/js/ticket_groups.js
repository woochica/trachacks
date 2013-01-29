jQuery.fn.createGroupedDataTable = function(){
      return this.dataTable({
        "bJQueryUI": true,
        "sPaginationType": "full_numbers",
        "fnDrawCallback": function ( oSettings ) {
          if ( oSettings.aiDisplay.length == 0 )
          {
            return;
          }
             
          var nTrs = $('#manage_ticket_fields tbody tr');
          var iColspan = nTrs[0].getElementsByTagName('td').length;
          var sLastGroup = "";
          for ( var i=0 ; i<nTrs.length ; i++ )
          {
            var iDisplayIndex = oSettings._iDisplayStart + i;
            var sGroup = oSettings.aoData[ oSettings.aiDisplay[iDisplayIndex] ]._aData[1];
            if ( sGroup != sLastGroup )
            {
                var nGroup = document.createElement( 'tr' );
                var nCell = document.createElement( 'td' );
                nCell.colSpan = iColspan;
                nCell.className = "group";
                nCell.innerHTML = sGroup;
                nGroup.appendChild( nCell );
                nTrs[i].parentNode.insertBefore( nGroup, nTrs[i] );
                sLastGroup = sGroup;
            }
          }
        },
        "aoColumnDefs": [
            { "bVisible": false, "aTargets": [ 1, 2 ] },
            { "bSortable": false, "aTargets": [ 0 ] }
        ],
        "aaSortingFixed": [[ 1, 'asc' ]],
        "aaSorting": [[ 2, 'asc' ]],
      });
};

/* Get the rows which are currently selected */
function fnGetSelected( oTableLocal )
{
  return oTableLocal.$('tr.row_selected');
}

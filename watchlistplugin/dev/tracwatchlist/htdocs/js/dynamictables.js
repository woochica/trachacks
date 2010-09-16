/*! Javsscript code for Trac Watchlist Plugin 
 * $Id: watchlist.js $
 * */

function wldeleterow(tr, table) {
  $(table).dataTable().fnDeleteRow(tr);
}

// Cookie Code taken from http://www.quirksmode.org/js/cookies.html
// 15th Sep 2010
// Changes: added path argument
function createCookie(name,value,days,path) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    if ( !path ) {
        path = "/";
    }
    document.cookie = name+"="+value+expires+"; path=" + path;
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ')
            c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0)
            return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name,"",-1);
}
/// End of Cookie Code

/*
$.fn.dataTableExt.afnFiltering.push(
    function( oSettings, aData, iDataIndex ) {
        var iColumn = 1;
        var table = $('#'+ oSettings.sTableId);
        var checked = $(table).find('input[name=sincelastvisit]').is(':checked');

        var n = document.createElement('div');
        n.innerHTML = aData[iColumn];
        timestamp = $(n).find('span.itime').text() * 1;

        if ( !timestamp ) {
            return true;
        }
        if ( checked && timestamp < $('#last_visit').val() ) {
            return false;
        }

        var iMin = $(table).find('input[name=from-datetime]').val() * 1;
        var iMax = $(table).find('input[name=to-datetime]').val() * 1;
        if ( !iMin && !iMax ) {
            return true;
        }
        else if ( !iMin && timestamp < iMax )
        {
            return true;
        }
        else if ( iMin < timestamp && !iMax )
        {
            return true;
        }
        else if ( iMin < timestamp && timestamp < iMax )
        {
            return true;
        }
        return false;
    }
);
*/

$.fn.dataTableExt.afnFiltering.push(
    function( oSettings, aData, iDataIndex ) {
        var iColumn = 1;
        var table = $('#'+ oSettings.sTableId);

        var show = true;
        $(table).find("span.datetimefilter").each( function () {
            var index = $(this).data('index');
            var checked = $(this).find('input[name=sincelastvisit]').is(':checked');
            if ( checked && aData[index-1] != '1' ) {
                show = false;
            }
            else {
                timestamp = aData[index+1] * 1;
                if ( !timestamp ) { return true; }
                var iMin = $(this).find('input[name=from-datetime-ts]').val() * 1;
                var iMax = $(this).find('input[name=to-datetime-ts]').val() * 1;
                if ( !iMin && !iMax ) { }
                else if ( !iMin && timestamp < iMax ) { }
                else if ( iMin < timestamp && !iMax ) { }
                else if ( iMin < timestamp && timestamp < iMax ) { }
                else { show = false; }
            }
        });
        return show;
    }
);



jQuery(document).ready(function() {
  // Dynamic Table
  $("table.watchlist").each(function(){
    // Disabled sorting of marked columns (unwatch, notify, etc.)
    var aoColumns = [];
    $(this).find('thead th').each( function () {
      if ( $(this).hasClass( 'hidden' ) ) {
        aoColumns.push( { "bSortable": false, "bSearchable": false, "bVisible": false } );
      } else if ( $(this).hasClass( 'sorting_disabled' ) ) {
        aoColumns.push( { "bSortable": false, "bSearchable": false } );
      } else {
        aoColumns.push( null );
      }
    });
    /* // Fixed width for name column (nonfunctional)
    if (aoColumns[0] == null) {
      aoColumns[0] = {};
    }
    aoColumns[0]['sWidth'] = $(this).find('thead th.name').css('width');
    */
    // Activate dataTable
    $(this).dataTable({
    "bStateSave": true,
    "aoColumns": aoColumns,
    //"bAutoWidth": false,
    //"bJQueryUI": true,
    "sPaginationType": "full_numbers",
    "bPaginate": true,
    "sDom": 'ilpfrt',
    "sPagePrevious": "&lt;",
    "aLengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "&#8734;"]],
    //"sPaginationType": "full_numbers",
    // Remove empty table
    "fnHeaderCallback": function ( nRow, aaData, iStart, iEnd, aiDisplay ) {
         if (aaData.length == 0) {
            wlremoveempty( nRow );
         }
    },
    "oLanguage": {
      "sLengthMenu": "_MENU_",
      "sZeroRecords": "./.",
      "sInfo": "_START_-_END_ / _TOTAL_",
      "sInfoEmpty": "./.",
      "sInfoFiltered": "(_MAX_)",
      "sProcessing": "...",
      "sInfoPostFix": "",
      "sSearch": "",
      "sUrl": "",
      "oPaginate": {
        "sFirst":    "|&lt;",
        "sPrevious": "&lt;",
        "sNext":     "&gt;",
        "sLast":     "&gt;|"
      },
      "fnInfoCallback": null
    },
   });
  });


  /* Per-column filters */
  $("table.watchlist").each( function () {
    var table  = this;
    var oTable = $(this).dataTable();

    /* Per-column filter input fields in footer */
    $(this).find("tfoot input.filter").keyup( function () {
      var index = $(table).find("tfoot th").index( $(this).parent("th") );
      oTable.fnFilter( this.value, index );
    });

    /* Restore per-column input values after page reload */
    var oSettings = oTable.fnSettings();
    $(this).find("tfoot th").each( function (i) {
      $(this).find("input.filter").val( oSettings.aoPreSearchCols[i].sSearch );
    });

    // Find index of column
    $(this).find("span.datetimefilter").each( function () {
        var index = $(this).parents('tfoot').find('th').index( $(this).parent("th") );
        $(this).data('index', index);
    });
    $(this).find("span.datetimefilter").each( function () {
        var dtfilter = this;
        $(this).find("input[name=sincelastvisit]").change( function () {
            if ( $(this).is(':checked') ) {
                $(dtfilter).find("input[type=text]").attr('disabled','disabled');
            } else {
                $(dtfilter).find("input[type=text]").removeAttr('disabled');
            }
            oTable.fnDraw();
        });
        $(this).find("input[type=text]").each( function () {
            $(this).AnyTime_picker({ format: "%Y-%m-%d %H:%i:%s" });
            $(this).change(function(){
                var c = new AnyTime.Converter({ format: "%Y-%m-%d %H:%i:%s" });
                $(this).next("input[type=hidden]").val( c.parse( $(this).val() ).getTime() / 1000 );
                oTable.fnDraw();
            });
        });
        // Restore datetime filter inputs on load
        // Must be after 'datetimefilter' handler are in place
        dtid = $(this).attr('id');
        $(this).find("input").each(function(){
            var name = dtid + '/' + $(this).attr('name');
            var value = readCookie(name);
            if ($(this).is("input[type=checkbox]")) {
                $(this).attr('checked', value =='checked' );
                $(this).change();
            }
            else {
                $(this).val(value);
                $(this).keyup();
            }
        });
    });
    oTable.fnDraw();
  });
});

/* Remove column sorting input when preferences are updated.
 * This is because the column order could have changed.
 * */
function wlprefsubmit(force){
  $("fieldset.orderadd").each( function () {
    if (force || $(this).data('modified')) {
      realm = $(this).data('realm');
      table = $("table#" + realm + "list");
      var oTable = $(table).dataTable();
      a = $(table).find("tfoot th");
      $(table).find("tfoot th").each( function (i) {
          oTable.fnFilter("",i);
      });
    }
  });
}


// Store datetime filter inputs on unload
jQuery(window).unload(function() {
    $(".datetimefilter").each(function(){
        dtid = $(this).attr('id');
        $(this).find("input").each(function(){
            var name = dtid + '/' + $(this).attr('name');
            var value = $(this).val();
            if ($(this).is("input[type=checkbox]")) {
                value = $(this).is(":checked") ? 'checked' : '';
            }
            createCookie(name,value,90,window.location.pathname);
        });
    });
});



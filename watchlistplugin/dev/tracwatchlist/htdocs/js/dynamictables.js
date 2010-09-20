/*! Javsscript code for Trac Watchlist Plugin
 * $Id: watchlist.js $
 * */

/*
 *  TypeWatch 2.0 - Original by Denny Ferrassoli / Refactored by Charles Christolini
 *
 *  Examples/Docs: www.dennydotnet.com
 *
 *  Copyright(c) 2007 Denny Ferrassoli - DennyDotNet.com
 *  Coprright(c) 2008 Charles Christolini - BinaryPie.com
 *
 *  Dual licensed under the MIT and GPL licenses:
 *  http://www.opensource.org/licenses/mit-license.php
 *  http://www.gnu.org/licenses/gpl.html
 *
 *  Modified by Martin Scharrer Sep 2010 to suit the Trac WatchlistPlugin.
 *  Changes:
 *      o Default values
 *      o Removed 'captureLength' code
 *      o Changed arguments to callback function.
 *      o Changed argument to typeWatch function from hash to callback function
 *        only
*/

(function(jQuery) {
    jQuery.fn.typeWatch = function(o){
        // Options
        var options = {
            wait : 555,
            callback : o,
            highlight : true,
        };

        function checkElement(timer, override) {
            var elTxt = jQuery(timer.el).val();

            // Fire if text > options.captureLength AND text != saved txt OR if override AND text > options.captureLength
            if (elTxt != timer.text || override) {
                timer.text = elTxt;
                timer.cb(timer.el,elTxt);
            }
        };

        function watchElement(elem) {
            // Must be text or textarea
            if (elem.type.toUpperCase() == "TEXT" || elem.nodeName.toUpperCase() == "TEXTAREA") {

                // Allocate timer element
                var timer = {
                    timer : null,
                    text : jQuery(elem).val().toUpperCase(),
                    cb : options.callback,
                    el : elem,
                    wait : options.wait
                };

                // Set focus action (highlight)
                if (options.highlight) {
                    jQuery(elem).focus(
                        function() {
                            this.select();
                        });
                }

                // Key watcher / clear and reset the timer
                var startWatch = function(evt) {
                    var timerWait = timer.wait;
                    var overrideBool = false;

                    if (evt.keyCode == 13 && this.type.toUpperCase() == "TEXT") {
                        timerWait = 1;
                        overrideBool = true;
                    }

                    var timerCallbackFx = function()
                    {
                        checkElement(timer, overrideBool)
                    }

                    // Clear timer
                    clearTimeout(timer.timer);
                    timer.timer = setTimeout(timerCallbackFx, timerWait);

                };

                jQuery(elem).keydown(startWatch);
            }
        };

        // Watch Each Element
        return this.each(function(index){
            watchElement(this);
        });

    };

})(jQuery);
///////////////

function wldeleterow(tr, table) {
  $(table).dataTable().fnDeleteRow(tr);
}

// Taken from http://datatables.net/forums/comments.php?DiscussionID=997
// Changes: TODO: also reset global filter
function fnResetAllFilters(oTable) {
    var oSettings = oTable.fnSettings();
    if (oSettings) {
        for(iCol = 0; iCol < oSettings.aoPreSearchCols.length; iCol++) {
            oSettings.aoPreSearchCols[ iCol ].sSearch = '';
        }
        oSettings.oPreviousSearch.sSearch = '';
        oTable.fnDraw();
    }
}
///

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
        path = "";
    }
    document.cookie = name+"="+value+expires+"; path=" + path + '/';
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

function eraseCookie(name,path) {
    createCookie(name,"",-1,path);
}
/// End of Cookie Code


jQuery.fn.dataTableExt.oSort['html-numeric-asc']  = function(x,y) {
    var a = parseFloat( x.replace(/<[^>]+>/g,'').replace(/^\s*#/,'') );
    var b = parseFloat( y.replace(/<[^>]+>/g,'').replace(/^\s*#/,'') );
    return ((a < b) ? -1 : ((a > b) ?  1 : 0));
};

jQuery.fn.dataTableExt.oSort['html-numeric-desc'] = function(x,y) {
    var a = parseFloat( x.replace(/<[^>]+>/g,'').replace(/^\s*#/,'') );
    var b = parseFloat( y.replace(/<[^>]+>/g,'').replace(/^\s*#/,'') );
    return ((a < b) ?  1 : ((a > b) ? -1 : 0));
};


$.fn.dataTableExt.afnFiltering.push(
    function( oSettings, aData, iDataIndex ) {
        var table = $('#'+ oSettings.sTableId);

        var show = true;
        $(table).find("span.datetimefilter").each( function () {
            if (!show) { return; }
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
        if (!show) { return false; }
        $(table).find("input.numericfilter").each( function () {
            if (!show) { return; }
            var index = $(this).data('index');
            var value = aData[index].replace(/<[^>]+>/g,'').replace('#','');
            var func  = $(this).data('filterfunction');
            if (func && !func(value)) {
                show = false;
            }
        });

        return show;
    }
);



jQuery(document).ready(function() {
  // Copy reset filter button (hidden in HTML code to avoid JS localisation)
  var resetfilters = $('#resetfilters').removeAttr('Id').removeAttr('style').detach();
  // Dynamic Table
  $("table.watchlist").each(function(){
    var table = this;
    // Disabled sorting of marked columns (unwatch, notify, etc.)
    var aoColumns = [];
    $(this).find('thead th').each( function () {
      if ( $(this).hasClass( 'hidden' ) ) {
        aoColumns.push( { "bSortable": false, "bSearchable": false, "bVisible": false } );
      } else {
      if ( $(this).hasClass( 'sorting_disabled' ) ) {
        aoColumns.push( { "bSortable": false, "bSearchable": false } );
      } else {
      if ( $(this).hasClass( 'filtering_disabled' ) ) {
        aoColumns.push( { "bSearchable": false, "sType": "html-numeric" } );
      } else {
        aoColumns.push( null );
      }}}
    });
    /* // Fixed width for name column (nonfunctional)
    if (aoColumns[0] == null) {
      aoColumns[0] = {};
    }
    aoColumns[0]['sWidth'] = $(this).find('thead th.name').css('width');
    */
    // Find index of column (must be done before .dataTable() so all hidden
    // columns are still in the DOM
    $(this).find("span.datetimefilter").each( function () {
        var index = $(this).parents('tfoot').find('th').index( $(this).parent("th") );
        $(this).data('index', index);
    });
    $(this).find("tfoot input.filter,tfoot input.numericfilter").each( function () {
      var index = $(table).find("tfoot th").index( $(this).parent("th") );
      $(this).data('index', index);
    });
    // Activate dataTable
    $(this).dataTable({
    "bStateSave": true,
    "sCookiePrefix": 'tracwatchlist_',
    "aoColumns": aoColumns,
    //"bAutoWidth": false,
    //"bJQueryUI": true,
    "sPaginationType": "full_numbers",
    "bPaginate": true,
    "sDom": 'ilp<"resetfilters">frt',
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
    var rfb = $(resetfilters).clone();
    $(rfb).click(function(){
        wldelfilters(table);
        return false;
    });
    $(table).parent().find("div.resetfilters").append( rfb );
  });
  $(resetfilters).remove();


  /* Per-column filters */
  $("table.watchlist").each( function () {
    var table  = this;
    var oTable = $(this).dataTable();

    /* Per-column filter input fields in footer */
    $(this).find("tfoot input.filter").keyup( function () {
      oTable.fnFilter( this.value, $(this).data('index') );
    });
    $(this).find("tfoot input.numericfilter").typeWatch(function (elem,text) {
      $(elem).data('filterfunction', wlgetfilterfunctions( text ));
      oTable.fnDraw();
    });


    /* Restore per-column input values after page reload */
    var oSettings = oTable.fnSettings();
    $(this).find("tfoot th").each( function (i) {
      $(this).find("input.filter").val( oSettings.aoPreSearchCols[i].sSearch );
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
function wldelfilters(table) {
    var oTable = $(table).dataTable();
    $(table).find('tfoot input[type=text],tfoot input[type=hidden]').removeAttr('disabled').val('');
    $(table).find('tfoot input.numericfilter').data('filterfunction','');
    $(table).parent().find('.dataTables_filter input').val('');
    $(table).find('tfoot input[type=checkbox]').removeAttr('checked');
    fnResetAllFilters(oTable);
    return true;
}

function wlprefsubmit(force){
  $("fieldset.orderadd").each( function () {
    if (force || $(this).data('modified')) {
      realm = $(this).data('realm');
      table = $("table#" + realm + "list");
      var oTable = $(table).dataTable();
      fnResetAllFilters(oTable);
    }
  });
}

// Store datetime filter inputs on unload
function wlstoredatetime() {
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
};
jQuery(window).unload(wlstoredatetime);

function wldeletecookies() {
    // Delete all datetime filter cookies
    $(".datetimefilter").each(function(){
        dtid = $(this).attr('id');
        $(this).find("input").each(function(){
            var name = dtid + '/' + $(this).attr('name');
            eraseCookie(name,window.location.pathname);
        });
    });
    // Delete all dataTable cookies
    // This might break if dataTables changes the internal names
    // of the cookie (last part of path is attached at the moment).
    // Some code copied from dataTables.js.
    $(".watchlist").each(function(){
        var id = $(this).attr('id');
        var aParts = window.location.pathname.split('/');
        var name = 'tracwatchlist_' + id + '_' + aParts.pop().replace(/[\/:]/g,"").toLowerCase();
        eraseCookie(name,aParts.join('/'));
    })

};

function wlresettodefault(){
    wlprefsubmit(1);
    // Disable storing of new cookies
    jQuery(window).unbind('unload',wlstoredatetime);
    // Remove all old cookies
    wldeletecookies();
}


// Creates a function which tests if the argument lies in the range by str.
// Examples:
//   'a-b' -> between a and b (both inclusive)
//   ' -b' -> lesser or equal than b  (identical to '0-b')
//   'a- ' -> greater or equal than a (identical to 'a-MAX_VALUE')
//   ' - ' -> all (identical to '0-MAX_VALUE')
//
function wlgetfilterfunction(str) {
    var i = str.indexOf ('-');
    var a; var b;
    if (i == -1) {
        a = parseFloat(str);
        b = a;
    }
    else {
        a = parseFloat( str.substring (0, i) );
        b = parseFloat( str.substring (i + 1) );
    }

    if (isNaN(a)) {
        a = 0;
    }
    if (isNaN(b)) {
        b = Number.MAX_VALUE;
    }
    if (a==b) {
        return function (num) { return (num == a); };
    } else {
        return function (num) { return ((num >= a) && (b >= num)); };
    }
}

// Returns a function with an array of the above functions.
// It returns true if any of them return true.
// Example: 'a-b,c-d' -> between a and b OR between c and d
function wlgetfilterfunctions(str) {
    var afunc = new Array();
    var parts = str.split(',')
    for (s in parts) {
        afunc.push( wlgetfilterfunction( parts[s] ) );
    }
    if (afunc.length == 1) {
        return afunc[0];
    }
    return function (num) {
        var i;
        for (i in afunc) {
            if (afunc[i](num)) {
                return true;
            }
        }
        return false;
    };
}



/*! Javascript code for Trac Watchlist Plugin
 * $Id$
 * */

/*!
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
// Changes: also reset global filter
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

// Initialise main cookie.
// If stored cookie is from an old version delete it.
var TRACWATCHLIST_COOKIE_VERSION = 1;
var maincookie = "TracWatchlistPlugin";
$.Jookie.Initialise(maincookie, 90*24*60);
if (!($.Jookie.Get(maincookie, "version") == TRACWATCHLIST_COOKIE_VERSION)) {
    var cookies = $.Jookie.Get(maincookie, "cookies");
    if (typeof(cookies) == 'Object') {
        for (cookie in cookies) {
            $.Jookie.Delete(cookie);
        }
    }
    $.Jookie.Delete(maincookie);
    $.Jookie.Initialise(maincookie, 90*24*60);
    $.Jookie.Set(maincookie, "version", TRACWATCHLIST_COOKIE_VERSION);
    $.Jookie.Set(maincookie, "cookies", new Object());
}
///

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
                else if ( !iMin && timestamp <= iMax ) { }
                else if ( iMin <= timestamp && !iMax ) { }
                else if ( iMin <= timestamp && timestamp <= iMax ) { }
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
  try {
     var resetfilters = $('#resetfilters').detach().removeAttr('Id').removeAttr('style');
  } catch (err) {
     var resetfilters = $('#resetfilters').clone().removeAttr('Id').removeAttr('style');
     $('#resetfilters').remove();
  }
  // Enable 'Delete Cookies' button
  $("#preferences form #deletecookies").click(function(){
      wldeletecookies();
      wldisablecookies();
      window.location.href =  window.location.protocol + '//' + window.location.host + window.location.pathname;
  });

  var cookies = $.Jookie.Get(maincookie, "cookies");
  if (typeof(cookies) != 'Object') {
    cookies = new Object();
  }

  // Dynamic Table
  $("table.watchlist").each(function(){
    var table = this;
    var tid = $(table).attr('id');

    // Init cookie for this table.
    // Update list of table cookies in main cookie.
    var cookie = "TracWatchlistPlugin-table#" + tid;
    $.Jookie.Initialise(cookie, 90*24*60);
    cookies[cookie] = 1;

    // Disabled sorting of marked columns (unwatch, notify, etc.)
    var asColumnNames = [];
    var aoColumns = [];
    $(this).find('thead th').each( function (i) {
      asColumnNames.push( String($(this).text()).replace(/^\s+|\s+$/g, '') );
      var hash = new Object();
      if ( $(this).hasClass( 'hidden' ) ) {
        hash["bVisible"] = false;
        hash["bSortable"] = false;
        hash["bSearchable"] = false;
      }
      if ( $(this).hasClass( 'sorting_disabled' ) ) {
        hash["bSortable"] = false;
        hash["bSearchable"] = false;
      }
      if ( $(this).hasClass( 'filtering_disabled' ) ) {
        hash["bSearchable"] = false;
        hash["sType"] = "html-numeric"
      }
      if ( $(this).hasClass( 'sort_next' ) ) {
        hash["iDataSort"] = i + 1;
      }
      aoColumns.push( hash );
    });
    // Check if columns (i.e. their order) changed:
    if (JSON.stringify(asColumnNames) != JSON.stringify($.Jookie.Get(cookie, "asColumnNames", asColumnNames))) {
        // If so delete cookie (and recreate it) to wipe the outdated settings:
        wldeletecookies("table#" + tid);
        $.Jookie.Initialise(cookie, 90*24*60);
    }
    // Store column names in cookie to check at next reload
    $.Jookie.Set(cookie, "asColumnNames", asColumnNames);

    /* // Fixed width for name column (nonfunctional)
    if (aoColumns[0] == null) {
      aoColumns[0] = {};
    }
    aoColumns[0]['sWidth'] = $(this).find('thead th.name').css('width');
    */
    // Find index of column (must be done before .dataTable() so all hidden
    // columns are still in the DOM
    $(this).find("tfoot th").each( function (index) {
        $(this).data('index', index);
    });
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
  $.Jookie.Set(maincookie, "cookies", cookies);
  $(resetfilters).remove();

  var use_datetime_picker = false;
  if ($('#datetime_format').length != 0) {
    use_datetime_picker = true;
    var datetime_format = $('#datetime_format').val();
    var datetime_picker_options = {
        'format' : datetime_format,
        'formatUtcOffset': "%: (%@)",
        'labelHour' : $('#labelHour').val(),
        'labelMinute' : $('#labelMinute').val(),
        'labelSecond' : $('#labelSecond').val(),
        'labelYear' : $('#labelYear').val(),
        'labelMonth' : $('#labelMonth').val(),
        'labelDayOfMonth' : $('#labelDayOfMonth').val(),
        'labelTimeZone' : $('#labelTimeZone').val(),
        'labelTitle' : $('#labelTitle').val(),
        'monthAbbreviations' : $('#monthAbbreviations').val().split(','),
        'dayAbbreviations' : $('#dayAbbreviations').val().split(','),
    };
    var tzoffset = $('#tzoffset').val() * 1;
    var datetime_converter_options = {
        'format' : datetime_format,
        'utcFormatOffsetImposed' : tzoffset,
        'utcParseOffsetAssumed'  : tzoffset,
    };
  }

  /* Per-column filters */
  $("table.watchlist").each( function () {
    var table  = this;
    var oTable = $(this).dataTable();
    var tid = $(table).attr('id');
    var cookie = "TracWatchlistPlugin-table#" + tid;

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
    $(this).find("tfoot th").each( function () {
      var index = $(this).data('index');
      $(this).find("input.filter").val( oSettings.aoPreSearchCols[index].sSearch );
    });

    /* Restore special numeric filters */
    $(table).find("tfoot input.numericfilter").each(function () {
        var name = tid + '/' + $(this).attr('name');
        var value = $.Jookie.Get(cookie, name);
        if (value) {
            $(this).val(value);
            $(this).data('filterfunction', wlgetfilterfunctions( value ));
        }
    });

    /* Restore special datetime filters */
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
        if (use_datetime_picker) {
            $(this).find("input[type=text]").each( function () {
                $(this).AnyTime_picker(datetime_picker_options);
                $(this).data('converter', new AnyTime.Converter(datetime_converter_options) );
                $(this).change(function(){
                    wlupdatedatetime(this);
                    oTable.fnDraw();
                });
            });
        }
        else {
            $(this).find("input[type=text]").typeWatch(function(elem,text){
                var timestamp =  Date.parse( text );
                $(elem).next("input[type=hidden]").val( timestamp / 1000 );
                oTable.fnDraw();
            });
        }
        // Restore datetime filter inputs on load
        // Must be after 'datetimefilter' handler are in place
        dtid = $(this).attr('id');
        $(this).find("input[type=text]").each(function(){
            var name = dtid + '/' + $(this).attr('name');
            var value = $.Jookie.Get(cookie, name);
            if (value) {
                $(this).val(value);
                $(this).change();
            }
        });
        $(this).find("input[type=checkbox]").each(function(){
            var name = dtid + '/' + $(this).attr('name');
            var value = $.Jookie.Get(cookie, name);
            if (value) {
                $(this).attr('checked', value =='checked' );
                $(this).change();
            }
        });
    });
    oTable.fnDraw();

    jQuery(window).bind('unload.watchlist.table#'+tid,function(){wlstorespecialfilters('table#' + tid)});
  });
});

function wlupdatedatetime(input) {
    var conv = $(input).data('converter');
    $(input).next("input[type=hidden]").val( conv.parse( $(input).val() ).getTime() / 1000 );
}

/* Remove column sorting input when preferences are updated.
 * This is because the column order could have changed.
 * */
function wldelfilters(table) {
    var oTable = $(table).dataTable();
    $(table).find('tfoot .datetimefilter input[type=text]').each(function() {
        $(this).removeAttr('disabled');
        $(this).val( $(this).prev().val() );
        wlupdatedatetime(this);
    });
    $(table).find('tfoot input.filter,tfoot input.numericfilter').removeAttr('disabled').val('');
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
      table = "table#" + realm + "list";
      wldeletecookies(table);
      wldisablecookies(table);
    }
  });
}

// Store datetime filter inputs on unload
function wlstorespecialfilters(tables) {
    if (!tables) { tables = "table.watchlist"; }
    $(tables).each( function () {
        table = this;
        var tid = $(table).attr('id');
        var cookie = "TracWatchlistPlugin-table#" + tid

        $(table).find("tfoot input.numericfilter").each(function () {
            var value = $(this).val();
            var name = tid + '/' + $(this).attr('name');
            $.Jookie.Set(cookie, name, value);
        });
        $(table).find(".datetimefilter").each(function(){
            var dtid = $(this).attr('id');
            $(this).find("input[type=text]").each(function(){
                var name = dtid + '/' + $(this).attr('name');
                var value = $(this).val();
                var initval = $(this).prev().val();
                if (value == initval) {
                    $.Jookie.Unset(cookie, name);
                }
                else {
                    $.Jookie.Set(cookie, name, value);
                }
            });
            $(this).find("input[type=checkbox]").each(function(){
                var name = dtid + '/' + $(this).attr('name');
                var value = $(this).is(":checked") ? 'checked' : '';
                $.Jookie.Set(cookie, name, value);
            });
        });
    });
};

function wldeletecookies(tables) {
    if (!tables) { tables = "table.watchlist"; }
    $(tables).each( function () {
        var tid = $(this).attr('id');
        var cookie = "TracWatchlistPlugin-table#" + tid;
        $.Jookie.Delete(cookie);
        // Delete all dataTable cookies
        // This might break if dataTables changes the internal names
        // of the cookie (last part of path is attached at the moment).
        // Some code copied from dataTables.js.
        var aParts = window.location.pathname.split('/');
        var name = 'tracwatchlist_' + tid + '_' + aParts.pop().replace(/[\/:]/g,"").toLowerCase();
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=' + aParts.join('/')+"/";
    });
};

// Disable creation of new cookies
function wldisablecookies(tables) {
    if (!tables) {
        tables = "table.watchlist";
        namespace = '.watchlist';
    }
    else {
        namespace = '.' + tables;
    }
    jQuery(window).unbind('unload' + namespace);
    $(tables).each( function () {
        var oTable = $(this).dataTable();
        var oSettings = oTable.fnSettings();
        oSettings.oFeatures.bStateSave = false;
    });
}

function wlresettodefault(){
    wlprefsubmit(1);
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
    if (!str) { str = ''; }
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



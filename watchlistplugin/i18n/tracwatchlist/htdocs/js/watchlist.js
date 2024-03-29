/*! Javsscript code for Trac Watchlist Plugin 
 * $Id: watchlist.js $
 * */


/*! From http://chris-barr.com/entry/disable_text_selection_with_jquery/  */
$(function(){
  $.extend($.fn.disableTextSelect = function() {
    return this.each(function(){
      if($.browser.mozilla){//Firefox
        $(this).css('MozUserSelect','none');
      }else if($.browser.msie){//IE
        $(this).bind('selectstart',function(){return false;});
      }else{//Opera, etc.
        $(this).mousedown(function(){return false;});
      }
    });
  });
  $('.noSelect').disableTextSelect();//No text selection on elements with a class of 'noSelect'
});
/*! */

function wlremoveempty( child ) {
    tdiv = $(child).parents('div.watchlist-parent').get(0);
    pdiv = $(tdiv).parent("div");
    $(tdiv).remove();
    $(pdiv).find('h2').removeClass('foldable');
    $(pdiv).find('p.noentrymessage').css('display','block');
    wlremmsgbox();
}

function wldeleterow(tr, table) {
  $(tr).remove();
}

function wlremmsgbox() {
  $('#message-box').remove();
}

jQuery(document).ready(function() {
  $("input.ackmsg").each(function() {
    $(this).disableTextSelect();
    $(this).click(function() {
      $(this).parents('div.system-message').hide(5).remove();
      return false;
    });
  });

  $("td.unwatch a.plainlink").each(function() {
    $(this).click(function() {
        tr    = $(this).parents('tr').get(0);
        table = $(tr).parents('table').get(0);
        $.ajax({ url: $(this).attr('href') + '&async=true', success: function (data, textStatus) {
            wldeleterow(tr, table);
          }
        });
        return false;
    });
  });
  $("td.notify a.plainlink").each(function() {
    $(this).click(function() {
        chkbox = $(this).children('input');
        $.ajax({ url: $(this).attr('href') + '&async=true', success: function (data, textStatus) {
          if ($(chkbox).attr('checked')) {
            $(chkbox).removeAttr('checked');
          }
          else {
            $(chkbox).attr('checked','checked');
          }
        } } );
        return false;
    });
  });

  $(".foldable").enableFolding(false, false, true);
//  $("table.watchlist").each(function() { wlchecktable(this); });
});



/*! Javascript code for Trac Watchlist Plugin 
 * $Id$
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

// The following functions will be overwritten by 'dynamictables.js' if loaded
function wldeleterow(tr, table) {
  $(tr).remove();
}

function wlresettodefault() {}
///

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
        a = this;
        chkbox = $(this).children('input');
        $.ajax({ url: $(this).attr('href') + '&async=true', success: function (data, textStatus) {
          if ($(chkbox).attr('checked')) {
            $(a).attr('href', $(a).attr('href').replace('action=notifyoff', 'action=notifyon') )
            $(chkbox).removeAttr('checked');
          }
          else {
            $(a).attr('href', $(a).attr('href').replace('action=notifyon', 'action=notifyoff') )
            $(chkbox).attr('checked','checked');
          }
        } } );
        return false;
    });
  });

  $(".foldable").enableFolding(false, false, true);
//  $("table.watchlist").each(function() { wlchecktable(this); });

  $("a.newwindow").click(function(){
      window.open(this.href);
      return false;
  });
  $("td a.more").click(function(){
      $(this).hide();
      $(this).parent().find(".moretext,.less").show();
  });
  $("td a.less").click(function(){
      $(this).hide();
      $(this).parent().find(".moretext").hide();
      $(this).parent().find(".more").show();
  });
  // Unfold section if context navigation link to it was used:
  $("div#ctxtnav a").click(function(){
      $( $(this).attr("href") + ' div.collapsed' ).removeClass("collapsed");
      return true;
  });
  // Unfold section if targeted directly by the URL
  if ( location.hash ) {
    $( location.hash + ' div.collapsed' ).removeClass("collapsed");
  }
});


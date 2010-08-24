/*! Javsscript code for Trac Watchlist Plugin 
 * $Id: watchlist.dev.js 8023 2010-05-28 19:45:13Z martin_s $
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


function wlshowhide(ref, tag) {
    $(tag).toggle("normal");

    if ($(ref).text() == "(Show)") {
      $(ref).text("(Hide)");
    }
    else {
      $(ref).text("(Show)");
    }
    return true;
}

jQuery(document).ready(function() {

  $("div#wlsettings").hide();

  $("#wikis span.showhide").text("(Hide)").disableTextSelect();
  $("#tickets span.showhide").text("(Hide)").disableTextSelect();
  $("#settings span.showhide").text("(Show)").disableTextSelect();
  $("#settings form").hide();

  $("#wikis span.showhide").click(function() {
     wlshowhide(this, "#wikilist-parent");
     return true;
  });

  $("#tickets span.showhide").click(function() {
     wlshowhide(this, "#ticketlist-parent");
     return true;
  });

  $("#settings span.showhide").click(function() {
     wlshowhide(this, "#settings form");
     return true;
  });


  $("input.ackmsg").each(function() {
    $(this).disableTextSelect().click(function() {
      $('#message-box').hide(5).remove();
      return false;
    });
  });

  $("td.unwatch a.plainlink").each(function() {
    $(this).click(function() {
        tr = $(this).parents('tr');
        $.ajax({ url: $(this).attr('href') + '&async=true', success: function (data, textStatus) { $(tr).remove(); } } );
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

});


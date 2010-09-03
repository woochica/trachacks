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

  $("#wikilist").tablesorter({widthFixed:true,headers: {
    4: {sorter:false}, 5: {sorter:false}, 6: {sorter:false}
  }
  }).tablesorterPager({container:$("#wikipager")}); 
  $("#ticketlist").tablesorter({widthFixed:true,headers: {
    4: {sorter:false}
  }
  }).tablesorterPager({container:$("#ticketpager")});
});



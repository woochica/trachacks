/*! Javascript code for Trac Watchlist Plugin
 * $Id$
 * */

function orderadd_buttons(orderadd, select1, select2 ) {
  $(orderadd).find("button[name=up]").click(function(){
    $(orderadd).data('modified', 1);
    $(select1).find("option:selected").each(function(){
      prev = $(this).prev();
      $(this).insertBefore(prev);
    });
  });
  $(orderadd).find("button[name=down]").click(function(){
    $(orderadd).data('modified', 1);
    $(select1).find("option:selected").each(function(){
      next = $(this).next();
      $(this).insertAfter(next);
    });
  });
  $(orderadd).find("button[name=right]").click(function(){
    $(orderadd).data('modified', 1);
    $(select2).append( $(select1).find("option:selected") );
  });
  $(orderadd).find("button[name=left]").click(function(){
    $(orderadd).data('modified', 1);
    $(select1).append( $(select2).find("option:selected") );
  });
}

// The following functions will be overwritten by 'dynamictables.js' if loaded
function wlprefsubmit(){}
function wlresettodefault(){}
///

$(document).ready(function(){
  $("#preferences form").submit(function(){
    $(".orderadd").each(function(){
      var text = [];
      $(this).find("select.active_fields option").each(function(){
        text.push( $(this).val() );
      });
      $(this).find("input.choosen_fields").val( text.join(',') );
    });
    wlprefsubmit();
    return true;
  });
  $("#preferences form input[type=reset]").click(function(){
    $(".orderadd select").each(function(){
        $(this).empty();
        $(this).append( $(this).data('original options') );
    });
    return true;
  });
  $("#preferences form #resettodefault").click(function(){
    form = $("#preferences form");
    $(form).find("input[name=action]").val("defaultsettings");
    wlresettodefault();
    $(form).submit();
    return false;
  });
  $(".orderadd select").each(function(){
      $(this).data('original options', $(this).find("option").clone() );
  });
  $(".orderadd").each(function(){
    realm = $(this).attr("id").replace("_fields","");
    $(this).data('realm', realm);
    select1 = $(this).find("select.active_fields");
    select2 = $(this).find("select.available_fields");
    orderadd_buttons(this, select1, select2 );
  });
});


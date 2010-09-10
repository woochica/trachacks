function orderadd_buttons(orderadd, select1, select2 ) {
  $(orderadd).find("button[name=up]").click(function(){
    $(select1).find("option:selected").each(function(){
      prev = $(this).prev();
      $(this).insertBefore(prev);
    });
  });
  $(orderadd).find("button[name=down]").click(function(){
    $(select1).find("option:selected").each(function(){
      next = $(this).next();
      $(this).insertAfter(next);
    });
  });
  $(orderadd).find("button[name=right]").click(function(){
    $(select2).append( $(select1).find("option:selected") );
  });
  $(orderadd).find("button[name=left]").click(function(){
    $(select1).append( $(select2).find("option:selected") );
  });
}

function wlprefsubmit(){}

$(document).ready(function(){
  $("#preferences form").submit(function(){
    $(".orderadd").each(function(){
      var text = [];
      $(this).find("select.active_columns option").each(function(){
        text.push( $(this).val() );
      });
      $(this).find("input.choosen_columns").val( text.join(',') );
    });
    wlprefsubmit();
    return true;
  });
  $(".orderadd").each(function(){
    select1 = $(this).find("select.active_columns");
    select2 = $(this).find("select.available_columns");
    orderadd_buttons(this, select1, select2 );
  });
});

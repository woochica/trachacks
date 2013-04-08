
// not exactly sure why this is required, but it didnt work in two
// browsers before adding it and it did after
window.setTimeout(function(){
  jQuery(document).ready(function(){
    // trac.12
    jQuery('.reports > tbody > tr').each(function(){
      if($(this).text().indexOf('Ticket Hours')>0
         || $(this).text().indexOf('Work Summary')>0
        ) $(this).detach();
    });
    //trac1.0
    jQuery('.reports > div.collapsed').each(function(){
      if($(this).text().indexOf('Management Screen')>0) $(this).detach();
    });
  });
},250);
jQuery(document).ready(function() { 
  jQuery("div.spoiler").hide();
  jQuery("span.spoiler").hide();
  jQuery('<a class="reveal">Reveal Spoiler &gt;&gt;</a>').insertBefore('.spoiler');
  jQuery('<a class="revealall">Reveal All Spoilers&gt;&gt;</a>').insertAfter('div.wikipage');
  jQuery('<a class="hideall">Hide All Spoilers&gt;&gt;</a>').insertAfter('a.revealall');
  jQuery('a.hideall').css('display', 'none');
  jQuery("a.revealall").click(function(){
    jQuery(this).fadeOut(600);
    jQuery('a.hideall').fadeIn(1200);
    jQuery('a.reveal').each(function(index) {
      jQuery(this).click()
    });
  });
  jQuery("a.hideall").click(function(){
    jQuery(this).fadeOut(600);
    jQuery('a.revealall').fadeIn(1200);
    jQuery('.spoiler').each(function(index) {
      jQuery(this).click()
    });
  });
  jQuery("a.reveal").click(function(){
    jQuery(this).next(".spoiler").fadeIn(1200);
    jQuery(this).next(".spoiler").css('display', 'inline');
    jQuery(this).next(".spoiler").css('background', '#ffcccc');
    jQuery(this).fadeOut(600);
  });
  jQuery(".spoiler").click(function(){
    jQuery(this).prev("a.reveal").fadeIn(1200);
    jQuery(this).fadeOut(600);
    jQuery(this).css('display','none');
  });
});


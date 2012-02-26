$(document).ready(function() { 
  $("div.spoiler").hide();
  $("span.spoiler").hide();
  $('<a class="reveal">Reveal Spoiler &gt;&gt;</a>').insertBefore('.spoiler');
  $("a.reveal").click(function(){
    $(this).next(".spoiler").fadeIn(1200);
    $(this).next(".spoiler").css('display', 'inline');
    $(this).fadeOut(600);
  });
  $(".spoiler").click(function(){
    $(this).prev("a.reveal").fadeIn(1200);
    $(this).fadeOut(600);
    $(this).css('display','none');
  });
});


$(document).ready(function() { 
  $("div.spoiler").hide();
  $('<a class="reveal">Reveal Spoiler &gt;&gt;</a>').insertBefore('.spoiler');
  $("a.reveal").click(function(){
    $(this).next("div.spoiler").fadeIn(1200);
    $(this).next("div.spoiler").css('display', 'inline');
    $(this).fadeOut(600);
  });
});


$(document).ready(function() { 
  $("div.spoiler").hide();
  $("span.spoiler").hide();
  $('<a class="reveal">Reveal Spoiler &gt;&gt;</a>').insertBefore('.spoiler');
  $('<a class="revealall">Reveal All Spoilers&gt;&gt;</a>').insertAfter('div.wikipage');
  $('<a class="hideall">Hide All Spoilers&gt;&gt;</a>').insertAfter('a.revealall');
  $('a.hideall').css('display', 'none');
  $("a.revealall").click(function(){
    $(this).fadeOut(600);
    $('a.hideall').fadeIn(1200);
    $('a.reveal').each(function(index) {
      $(this).click()
    });
  });
  $("a.hideall").click(function(){
    $(this).fadeOut(600);
    $('a.revealall').fadeIn(1200);
    $('.spoiler').each(function(index) {
      $(this).click()
    });
  });
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


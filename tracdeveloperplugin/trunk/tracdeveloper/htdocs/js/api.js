$(document).ready(function () {
  var once = true;
  $('.interface div, .component div').hide();
  $('a.implements').click(function () {
  var id = $(this).attr('href');

    $('.selected').removeClass('selected');
    $(id).addClass('selected');
  });
  $('#interfaces h3').each(function() {
    $(this).wrap('<a href="javascript:void(0)"></a>').click(function() {
    var root = this.parentNode.parentNode

      $(root).find('div').toggleClass('expanded').slideToggle();
      $('.selected').removeClass('selected');
      if ($(root).find('div').css('display') == 'none') {
        $(root).addClass('selected');
      }
    });
  });
  $('#components h3').each(function() {
    $(this).wrap('<a href="javascript:void(0)"></a>').click(function() {
    var root = this.parentNode.parentNode;

      $('.selected').removeClass('selected');
      if ($(root).find('div').css('display') == 'none') {
        $('.expanded').toggleClass('expanded').slideToggle();
        $(root).find('div').slideDown().addClass('expanded');
        $(root).find('a.implements').each(function () {
        var id = $(this).attr('href');

          $(id).find('div').slideDown().addClass('expanded');
        });
      } else {
        $('.expanded').slideUp().removeClass('expanded');
      }
    });
  });
});

var showToggle = "Show";
var hideToggle = "Hide";

$(document).ready(function() {
    $(".toggle_container").hide();

    $(".toggle_container").before("<div class='toggle-trigger'>[<a href='#'>"+ showToggle  +"</a>]</div>");

    $('.toggle-trigger').toggle(function() {
        var div = $(this).children();
        div.html(div.html().replace(showToggle, hideToggle));
    }, function() {
        var div = $(this).children();
        div.html(div.html().replace(hideToggle, showToggle));
    });

    $(".toggle-trigger").click(function() { 
        $(this).next(".toggle_container").slideToggle("slow,");
    });
});


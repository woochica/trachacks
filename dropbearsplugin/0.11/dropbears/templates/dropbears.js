function make_bear() {
    var y = Math.round(document.width * Math.random());
    var bear = $('<img class="dropbear" src="${href.chrome('dropbear', 'dropbear.gif')}" alt="DROPBEAR!" />');
    bear.css('left',y+'px').appendTo('body').animate({top:document.height}, 3000+Math.round(2000*Math.random()), 'linear', function(){
        $(this).remove();
        if(bear.attr('alt') != 'Dead bear') {
            make_bear();
        }
    }).hover(function(){
        bear.attr('alt','Dead bear');
        bear.attr('src', '${href.chrome('dropbear', 'dropbear-dead.gif')}')
    }, function(){});
}

$(function(){
#for i in xrange(dropbears)
    make_bear();
#end
});
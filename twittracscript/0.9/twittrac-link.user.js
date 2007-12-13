// ==UserScript==
// @name            twittraclink
// @namespace       tag:ento@ce-lab.net,2007-12-05:twittrac
// @description     add link to today's twittrac page
// @include         http://*trac*
// ==/UserScript==

(function(){
    var pad = function(n){
        return n > 9 ? ('' + n) : ('0' + n);
    };
    // get the main nav menu
    var nav = document.getElementById('mainnav');
    // get the link to wiki top
    var ul = nav.getElementsByTagName('ul')[0];
    var list = ul.getElementsByTagName('li');
    var wikilink = list[0].getElementsByTagName('a')[0];
    // prepare the twittrac url
    var today = new Date();
    var url = wikilink.getAttribute('href') + '/Twittrac/' + today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());
    // prepare the element to insert
    var link = document.createElement('a');
    var li = document.createElement('li');
    link.setAttribute('href', url);
    link.innerHTML = 'Twittrac';
    li.appendChild(link);
    // insert
    ul.insertBefore(li, list[1]);
})();

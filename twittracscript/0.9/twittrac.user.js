// ==UserScript==
// @name            twittrac
// @namespace       tag:ento@ce-lab.net,2007-12-05:twittrac
// @description     insert a simple add comment form
// @include         http*://*trac*wiki/Twittrac/*
// @include         http*://*trac*wiki/SandBox
// ==/UserScript==

(function(){

    
    function pad(n){
        return n > 9 ? ('' + n) : ('0' + n);
    }

    function onCurrentPageText(callback){
        var plainUrl = document.location + '?format=txt';
        GM_xmlhttpRequest({
            method: 'GET',
            url: plainUrl,
            onload: function(res) {
                callback(res.responseText.split('<!DOCTYPE')[0]);
            }
        });
    }

    function updatePage(){
        GM_xmlhttpRequest({
            method: 'GET',
            url: '' + document.location,
            onload: function(res) {
                var after = res.responseText.split('<div id="content" class="wiki">')[1];
                var before = after.split('<script type="text/javascript">searchHighlight()</script>')[0];
                document.getElementById('content').innerHTML = before;
            }
        });        
    }

    function getUsername(){
        // get the meta nav menu
        var nav = document.getElementById('metanav');
        var ul = nav.getElementsByTagName('ul')[0];
        var list = ul.getElementsByTagName('li');
        var match = list[0].innerHTML.match(/logged in as (.*)/);
        return match ? match[1] : 'foo';
    }

    function getVersion(){
        var deldiv = document.getElementById('delete');
        if (deldiv){
            var inputs = deldiv.getElementsByTagName('input');
            for(var i = 0; i < inputs.length; i++){
                if (inputs[i].getAttribute('name') == 'version') {
                    return parseInt(inputs[i].getAttribute('value'));
                }
            }
        }
        return 0;
    }

    function getTimeString(){
        var today = new Date();
        return pad(today.getHours()) + ':' + pad(today.getMinutes()) + ':' + pad(today.getSeconds());
    }

    function doSave(data){
        // GM_log('saving '  + data + ' in ' + document.location);
        GM_xmlhttpRequest({
            method: 'POST',
            url: '' + document.location,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded' 
            },
            data: data,
            onerror: function(res){
                GM_log('error: ' + res);
            },
            onload: function(res){
                document.getElementById('status').value = '';
                updatePage();
            }
         });
    }


    function doInsert(){
        var status = document.getElementById('status').value;
        if (!status) {
            updatePage();
            return;
        }
        var user = getUsername();
        var version = getVersion();
        var entry = formatEntry(status, user);
        onCurrentPageText(function(text){
            var data = 'scroll_bar_pos=&editrows=&readonly=&save=Submit+changes&action=edit';
            data += '&version=' + version;
            data += '&text=' + encodeURIComponent(insertEntryToText(entry, text));
            // data += '&comment=' + encodeURIComponent(status);
            data += '&author=' + encodeURIComponent(user);
            doSave(data);
        });
    }

    function formatEntry(status, user){
        var retval = ' ,,';
        retval += getTimeString();
        retval += ' ';
        retval += user;
        retval += ',, :: ';
        retval += status;
        retval += '\n';
        return retval;
    }

    function insertEntryToText(entry, text){
        var marker = '== twittrac ==';
        var split = text.split(marker);
        if (split.length < 2) {
            // no marker specified, prepend to the whole thing
            return entry + text;
        } else {
            // prepend to the second chunk
            split[1] = entry + split[1];
            return split.join(marker + "\n");
        }
    }
    
    // prepare the update form
    var div = document.createElement('div');
    div.setAttribute('id', 'twittrac');
    div.setAttribute('class', 'wikipage');
    div.setAttribute('style', 'text-align: center; padding: 1em;');

    var textarea = document.createElement('textarea');
    textarea.setAttribute('id', 'status');
    textarea.setAttribute('cols', '70');
    div.appendChild(textarea);

    var br = document.createElement('br');
    div.appendChild(br);

    var submit = document.createElement('input');
    submit.setAttribute('id', 'add');
    submit.setAttribute('type', 'button');
    submit.setAttribute('value', 'add');
    submit.addEventListener('click', doInsert, false);
    div.appendChild(submit);

    // insert
    var content = document.getElementById('content');
    content.parentNode.insertBefore(div, content);
})();

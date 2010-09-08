
var datasaver_initial;
var datasaver_loaded;

jQuery(
function datasaver($)
{
    // Keep a copy of the uninitialized data for comparison later.
    datasaver_initial = datasaver_capture()
    datasaver_loaded = datasaver_load()
    if (datasaver_loaded)
    {
        //datasaver_blink()
        $('#datasaver_restorer').addClass('restore_possible')
    }
    else
    {
        $('#datasaver_restorer').css('opacity', '0.25')
    }

    // Keep a copy of form data every minute and keep a copy if the page is 
    //datasaver_watcher()

    // Also track when the page is left.
    $(window).unload(datasaver_savior)
})

var datasaver_blink_state = 1.0;
var datasaver_blinking = true;
function datasaver_blink()
{
    if (datasaver_blinking)
    {
        jQuery('#datasaver_restorer').css('opacity', datasaver_blink_state);
        datasaver_blink_state = 1.0 - datasaver_blink_state;
        setTimeout(datasaver_blink, 500)
    }
}

function datasaver_check()
{
    // Look for saved form data.  If it's present, ask to load it.
    var formdough = datasaver_load()
    if (formdough)
    {
        if (confirm(_("There is previous form data present " +
                      "for this page. Do you want to restore it?")))
        {
            datasaver_restore(formdough);
        }
    }

}

function datasaver_watcher()
{
    datasaver_save();
    setTimeout(datasaver_watcher, 60000);
}

function datasaver_savior(event)
{
    datasaver_save()
}

function datasaver_clear()
{
    var path = document.location.pathname
    document.cookie = '__FORMDATA__=; path=' + path + '; ';
}

function datasaver_capture()
{
    // Scan all forms and collect an escaped version of the data.
    var formdata = []
    var formcount = document.forms.length;
    for (var formidx = 0; formidx < formcount; ++formidx)
    {
        var form = document.forms[formidx];
        var elemcount = form.elements.length;
        for (var elemidx = 0; elemidx < elemcount; ++elemidx)
        {
            var element = form.elements[elemidx];
            if (element.type != 'submit' && 
                element.type != 'hidden' &&
                element.value)
            {
                formdata.push(
                    formidx + ':' + elemidx + ':' + 
                    escape(element.value))
            }
        }
    }
    return formdata.join('&');
}
    
function datasaver_save(formdough)
{
    formdough = formdough || datasaver_capture()

    // Set a cookie in the document.
    if (formdough && formdough != datasaver_initial)
    {
        var path = document.location.pathname
        document.cookie = '__FORMDATA__=' + formdough + 
            '; path=' + path + '; '
    }
    else
    {
        datasaver_clear()
    }
}

function datasaver_load()
{
    // Look for a FORMDATA cookie element.
    var dough = document.cookie
    var formdataidx = dough.search('__FORMDATA__=')
    var formdough = '';
    if (formdataidx >= 0)
    {
        var formdough = dough.substr(formdataidx + 13)
        var formdataend = formdough.search(';')
        if (formdataend >= 0)
        {
            formdough = formdough.substr(0, formdataend)
        }
    }
    return formdough;
}

function datasaver_restore(formdough)
{
    formdough = formdough || datasaver_loaded
    if (formdough)
    {
        if (confirm(_("Are you sure you want to restore? " +
                      "Anything unsaved on this page will be lost!")))
        {
            // Break up dough at &'s
            var formdata = []
            var parts = formdough.split('&')
            var partcount = parts.length;
            for (var partidx = 0; partidx < partcount; ++partidx)
            {
                // Break each part at ;
                var bits = parts[partidx].split(':')
                var formidx = parseInt(bits[0])
                var elemidx = parseInt(bits[1])
                document.forms[formidx].elements[elemidx].value = 
                    unescape(bits[2])
            }
        }
        jQuery('#datasaver_restorer').css('opacity', '0.25')
        jQuery('#datasaver_restorer').removeClass('restore_possible')
        datasaver_blinking = false;
    }
    else
    {
        alert(_("No form data is available for restoration."))
    }
}


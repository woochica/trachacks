// settings
var refresh_interval = 5000; // 5 s
var request_timeout = 26000; // 26 s

var ticket_url;
var warning_sel = '#warning.system-message', form_sel = '#propertyform';
var submit_button_sel = ':submit[name=submit]', submit_button_text;
var buttons_sel = form_sel + ' div.buttons';
var properties_section_sel = '#properties';
var ticket_sel = '#ticket';
var attach_sel = '#attachments';
var changelog_sel = '#changelog';
var last_comment_sel = changelog_sel + ' .change p:last';
var comment_sel = '#comment';

function update_ui(clear_form, responseText, statusText) {
    if (statusText == 'success') {
	var $response = $(responseText);
	var selectors = [ticket_sel, attach_sel, changelog_sel];
	var update_changetime = function ($resp) {
	    var input_sel = 'input[name=ts]';
	    $(input_sel).replaceWith($(input_sel, $resp));
	};
	if ($(warning_sel, $response)[0]) {
	    // there is a warning in response - comment added after the last update
	    $.get(ticket_url, update_ui_get);
	    var $warning = $(warning_sel, $response);
	    $warning.html($warning.html() +
			  '. Please, review changes and submit the form again');
	    $(buttons_sel).before($warning);
	    reset_submit_button();
	    return;
	} else if (clear_form) {
	    // remove warning from current page, if there was no warning in $reponse
	    $(warning_sel).remove(); 
	} else if (
	    // there is a warning and the last comment in response is the same as
	    // the comment we entered - most likely we submitted the comment, but
	    // anyway the text won't be lost
	    $(warning_sel)[0] && comments_seem_equal(
		$(last_comment_sel, $response).text(), $(comment_sel).val())) {
	    clear_form = true; // than we can clear the form, and remove warning
	    $(warning_sel).remove();
	}
	if (clear_form)
	    selectors.push(form_sel);
	$.each(selectors, function (i, s) {$(s).replaceWith($(s, $response)); });
	if (!$(changelog_sel)[0] && $(changelog_sel, $response)[0]) {
	    // when there are no comments to the ticket, we have to add comments section
 	    $(attach_sel)
		.after($(changelog_sel, $response))
		.after($('<h2>Change History</h2>'));
	}

	if (clear_form) {
	    // Add the toolbar to all <textarea> elements on the page with the class
	    // 'wikitext': from wikitoolbar.js FIXME
	    if (window.addWikiFormattingToolbar != undefined) {
		$("textarea.wikitext").each(function() { addWikiFormattingToolbar(this) });
	    }
	    setup_form_handlers();
	} else { // update only ticket change time
	    var input_sel = 'input[name=ts]';
	    $(input_sel).replaceWith($(input_sel, $response));
	}
    }
}

function comments_seem_equal(s1, s2) {
    // Compare formatted and unformatted comments
    // we remove trac formatting from strings and compare them
    return strip_formatting(s1) == strip_formatting(s2);
}

var trac_formatting_symbols = ' \'"-=+*[]/{}~,.^!&,@#%:;|()\\`\n\t\r<>';
var trac_fs_regexp_str = '';
for (var i = 0; i < trac_formatting_symbols.length; i++) {
    trac_fs_regexp_str += '\\' + trac_formatting_symbols[i];
}
var trac_fs_regexp = new RegExp('[' + trac_fs_regexp_str + ']', 'g');


function strip_formatting(s) {
    // return copy of s without trac formatting symbols
    s = s.replace(/\[\[[^\]]*\]\]/g, ''); // remove [[...]]
    s = s.replace(/\[[^\]]*\]/g, ''); // remove [...]
    return s.replace(trac_fs_regexp, ''); // remove other symbols
}

function update_ui_get(responseText, statusText) {
    update_ui(false, responseText, statusText);
}

function update_ui_post(responseText, statusText) {
    update_ui(true, responseText, statusText);
}

var has_focus = true, refresh_on = false, just_loaded = true;

function refresh() {
    if (has_focus) {
	refresh_on = true;
	has_focus = false; // some action has to set has_focus to true
	$.get(ticket_url, update_ui_get);
	setTimeout(refresh, refresh_interval);
    } else { // stop refreshing if there was no activity in refresh_interval
	refresh_on = false;
    }
}

function on_ajax_error(request, error, exception) {
    $(buttons_sel).before($('<div id="warning" class="system-message">' +
			    'Connect to server failed: "' + error +
			    '". Trying to fetch comments</div>'));
    reset_submit_button();
}

function reset_submit_button() {
    var $button = $(submit_button_sel);
    $button.attr('disabled', '');
    $button.attr('value', submit_button_text);
}

function setup_form_handlers () {
    $(submit_button_sel).click(
	function () {
	    $(form_sel).ajaxSubmit(
		{success: update_ui_post, 
		 error: on_ajax_error,
		 timeout: request_timeout});
	    var $button = $(this);
	    submit_button_text = $button.attr('value');
	    $button.attr('disabled', 'true');
	    $button.attr('value', 'Wait, please...');
	    return false;
	});
    $(properties_section_sel + ' table').hide();
    $(properties_section_sel + ' legend').click(
	function () {
	    $(properties_section_sel + ' table').toggle();
	}
    );
}

$(document).ready(
    function () {
	if (!$('fieldset#preview')[0]) { // do not enchance ui on preview page
	    ticket_url = $(form_sel).attr('action');
	    setup_form_handlers();
	    
	    // polling for new comments:
	    // main idea here is to poll for them only when there is
	    // some activity on the page
	    $(window).mousemove(
		function () {
		    has_focus = true;
		    if (!just_loaded && !refresh_on) {
			// user enters a page that has not been visited for a while
			// => start refreshing again
			refresh();
		    }
		});
	    setTimeout(refresh, refresh_interval);
	    setTimeout(function () {just_loaded = false;}, 1.5 * refresh_interval);
	}
    }
);
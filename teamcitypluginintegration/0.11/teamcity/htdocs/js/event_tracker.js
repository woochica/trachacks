var pos = window.location.pathname.indexOf('/builds');
if (pos >= 0) {
	var base_url = window.location.pathname.substring(0,pos) + '/builds/';
} else {
	var base_url = 'builds/';
}
function build_selected(event) {
	$("input:checked").each(function() {
		var checkbox = this
		var bt_id = $(this).val();
		$.ajax({
			url: base_url + "proxy/action.html?agentId=allEnabledCompatible&add2Queue="+bt_id,
			success: function() {
				// remove "checked" from checkbox
				$(checkbox).removeAttr("checked");
				// hide this checkbox
				$(checkbox).hide();

			},
			error: show_error,
		});
	});
}

function get_running_builds() {
	$.ajax({
		url: base_url + "proxy/ajax.html?getRunningBuilds=1",
		dataType: "xml",
		success: function(response,t_status,xhr) {
			update_builds_status(response)
			$("div#info_ajax_error").hide();
		},
		error: show_error,
	});
}

function update_builds_status(xml) {
	var current_builds = $("build", xml);
	var all_builds = $("div.inner-build");
	var cur_btids = new Array();
	$(current_builds).each(function() {
		var bt_id = $(this).attr("buildTypeId");
		// update progressbar
		var pbar = $("div#progress-"+bt_id);
		var width = $(this).attr("completedPercent") * parseFloat($(pbar).parent().css("width"))/100;
		$("div#header-"+bt_id).removeClass("success").removeClass("failure").addClass("running");
		$(pbar).width(width);
		// set progress bar text
		var pbar_text = $("span#progress-text-"+bt_id);
		$(pbar_text).text('Remaining time: '+$(this).attr('remainingTime')+', '+$(this).attr('completedPercent')+'% complete');
		if ($(this).attr('exceededEstimatedDurationTime') != '< 1s') {
			$(pbar_text).text('Overtime: '+$(this).attr('exceededEstimatedDurationTime'));
		}
		$(pbar).parent().show();
		// hide checkbox
		$("input#box-"+bt_id).hide();
		// show 'Cancel build'
		$("a#cancel-"+bt_id).show();
		// set id to progressbar parent to build id
		var build_id = $(this).attr("buildId");
		$(pbar).parent().attr("id", build_id);
		// attach btid to cur_btids
		cur_btids.push(bt_id);
	});
	var html_running_builds = $("div.running");
	// cleanup ended builds here
	if (html_running_builds.length != current_builds.length) {
		// iterate over all html-runned builds and cleanup
		$(html_running_builds).each(function() {
			var html_btid = $(this).children("input").val();
			// search this buildTypeId in running builds
			if (!in_array(html_btid,cur_btids)) {
				//FIXME!
				location.reload();
			}
		});
	}
	// disable button if all builds was started
	if (current_builds.length >= all_builds.length) {
		$("#build-button").attr("disabled", "true");
	} else {
		$("#build-button").removeAttr("disabled");
	}
}

function in_array(what,where) {
	for (var i=0; i < where.length; i++) {
		if (what == where[i]) {
			return true;
		}
	}
	return false;
}

function show_error(xhr,t_status,err) {
	// build message from status and xhr.responseText
	msg = xhr.status+ " " + xhr.statusText;
	err_text = $(xhr.responseText).find('div.error p.message').text();
	msg = msg + ": " + err_text;
	$("div#info_ajax_error").text(msg);
	$("div#info_ajax_error").show();
}

function cancel_build(build_id) {
	$.ajax({
		url: base_url + "proxy/ajax.html?comment=TracCancel&submit=Stop&kill&buildId="+build_id,
		error: show_error,
	});
}

$(document).ready(function() {
	get_running_builds();
	$(this).everyTime(3000, get_running_builds, 0);
	$("button#build-button").click(build_selected);
	$("a.stop-build").click(function(event) {
		event.preventDefault();
		var build_id = $(this).siblings("div.build-info").attr('id');
		if (build_id != undefined) {
			cancel_build(build_id);
		}
	});
});

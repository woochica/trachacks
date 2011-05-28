if(!("console" in window)) 
    window.console = {log: function() {}};

var editorMode = "text";
//var editorMode = "wysiwyg";
var wysiwyg_count = 0;

function setupToggleEditorButtons() {
    var div = document.createElement("div");
//    var mode = TracWysiwyg.editorMode;
    
    var html = ''
    	+ '<div id="switch_editor">'
    	+ '<a id="wysiwyg_ck_switch" href="/">Switch to Wysiwyg (CKEditor) </a>'
    	+ '<a id="wysiwyg_text_switch" href="/">Switch to Plain Text Editor </a>'
    	+ '</div>'
        + '&nbsp; ';
    div.className = "editor-toggle";
    div.innerHTML=html;
    $("#rows").after(div);

    $("#wysiwyg_text_switch").hide();
    
    // Catch switch events.
    $("#wysiwyg_ck_switch").live("click", function() {
    	
    	switchToCKEditor();
    	
    	return false;
    });
    
    $("#wysiwyg_text_switch").live("click", function() {
    	
    	switchToTextEditor();
    	
    	return false;
    });
}

var editor;
function switchToCKEditor() {
	$("#wysiwyg_ck_switch").hide();
	$("#wysiwyg_text_switch").show();
	
	editorMode = "wysiwyg";
	unHtmlifyText();
	editor = CKEDITOR.replace("text");
}

function switchToTextEditor() {
	$("#wysiwyg_text_switch").hide();
	$("#wysiwyg_ck_switch").show();
	
	editorMode = "text";
	editor.destroy();
	htmlifyText();
}

/**
 * Adds the special trac signal for html from the textbox.
 */
function htmlifyText() {
	val = $("#text" ).val();
	newval = "{{{\n#!html\n\n" + val + "\n\n}}}";
	$("#text").val(newval);
}

/**
 * Removes the special trac signal for html from the textbox.
 */
function unHtmlifyText() {
	val = $("#text" ).val();
	newval = val.replace('{{{\n#!html\n\n','');
	newval = newval.replace('\n\n}}}', '');
	$("#text").val(newval);
}

function setupSubmission() {
	$("form#edit").submit(function (e) {
		if (editorMode == "wysiwyg") {
			switchToTextEditor();
		}
	});
}

jQuery(document).ready(function($) {
	setupToggleEditorButtons();
	setupSubmission();
});

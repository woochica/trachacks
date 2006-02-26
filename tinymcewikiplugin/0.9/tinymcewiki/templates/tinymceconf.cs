<script language="javascript" type="text/javascript" src="<?cs var:htdocs_location ?>tinymce/jscripts/tiny_mce/tiny_mce.js"></script>
<script language="javascript" type="text/javascript">
tinyMCE.init({
	mode : "textareas",
	//language : "ja",
	content_css : "<?cs var:htdocs_location ?>tinymce/tinymce_trac.css",
	theme : "advanced",
	plugins : "table,save,advhr,advimage,advlink,emotions,iespell,insertdatetime,preview,zoom,flash,searchreplace,print,contextmenu,paste,directionality,fullscreen,tracmacro",
	theme_advanced_buttons1_add_before : "save,newdocument,separator",
	theme_advanced_buttons1_add : "fontsizeselect",
	theme_advanced_buttons2_add : "separator,insertdate,inserttime,preview,zoom,separator,forecolor,backcolor",
	theme_advanced_buttons2_add_before: "cut,copy,paste,pastetext,pasteword,separator,search,replace,separator",
	theme_advanced_buttons3_add_before : "tablecontrols,separator",
	theme_advanced_buttons3_add : "emotions,iespell,flash,advhr,separator,print,separator,ltr,rtl,separator,fullscreen,tracmacro",
	theme_advanced_toolbar_location : "top",
	theme_advanced_toolbar_align : "left",
	theme_advanced_statusbar_location : "bottom",
    plugi2n_insertdate_dateFormat : "%Y/%m/%d",
    plugi2n_insertdate_timeFormat : "%H:%M:%S",
	extended_valid_elements : "hr[class|width|size|noshade],font[face|size|color|style],span[class|align|style]",
	external_link_list_url : "example_link_list.js",
	external_image_list_url : "example_image_list.js",
	flash_external_list_url : "example_flash_list.js",
	file_browser_callback : "fileBrowserCallBack",
	paste_use_dialog : false,
	theme_advanced_resizing : true,
	theme_advanced_resize_horizontal : false,
	theme_advanced_link_targets : "_something=My somthing;_something2=My somthing2;_something3=My somthing3;",
	paste_auto_cleanup_on_paste : true,
	paste_convert_headers_to_strong : false,
	paste_strip_class_attributes : "all"

});

function fileBrowserCallBack(field_name, url, type, win) {
	// This is where you insert your custom filebrowser logic
	alert("Filebrowser callback: field_name: " + field_name + ", url: " + url + ", type: " + type);

	// Insert new URL, this would normaly be done in a popup
	win.document.forms[0].elements[field_name].value = "someurl.htm";
}
</script>

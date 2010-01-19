function myDblClickHandler(event) {
  if (document.location.href.indexOf('?')>0) {
	var queryString = document.location.href.substr(document.location.href.indexOf('?') + 1);
	var params = queryString.split('&');
	if (queryString.indexOf('action=edit')>=0) {
			document.getElementById("save").click()
	}
  } else {
	document.location=document.location + "?action=edit";
  }
}
document.ondblclick = myDblClickHandler;

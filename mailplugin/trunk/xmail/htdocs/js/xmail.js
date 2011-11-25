function selectAllFields(/*String*/name, /*boolean*/checked) {
	if (checked == undefined || checked == null) {
		checked = true;
	}
	var checkboxes = document.getElementsByName(name);
	var i = 0;
	
	for (i = 0; i < checkboxes.length; i++) {
		checkboxes[i].checked = checked;
	}
}

function confirmSelection(/*Object*/selectForm, /*String*/selectList, /*String*/action, /*boolean*/confirm) {
	if (!selectForm)
		return false;
	
	var chkb = document.getElementsByName(selectList);
	if (!chkb)
		return false;
	
	var list = null;
	
	for (var i = 0; i < chkb.length; i++) {
		if (chkb[i].checked) {
			if (list) {
				list += ', ' + chkb[i].value
			} else {
				list = chkb[i].value
			}
		}
	}
	
	if (confirm) {
		confirm = window.confirm(action + ' filter ids ' + list + '?');
	} else {
		confirm = true;
	}
	
	if ( confirm ) {
//		alert ('try to submit!');
		selectForm.elements['xmailAction'].value = action
		selectForm.submit();
	} else {
		selectForm.reset();
	}
}
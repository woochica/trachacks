function onTypeChanged(evt) { 
	targetElem = document.getElementById('field-description');
	defaultElem = document.getElementById('description_default');
	typeElem = document.getElementById('field-type');
	
	sourceElem = document.getElementById('description_' + typeElem.selectedIndex);

	if (!sourceElem.value)
	{
		return
	}

	if (evt.type == "change")
	{
		answer = confirm("用模板的内容替换描述文字吗?");
		if (!answer)
		{
			return;
		}
	}

	if (sourceElem)
	{
		// update description textarea
		targetElem.value = sourceElem.value ? sourceElem.value : defaultElem.value;
	}

}

function onCustomChanged(evt) { 
	targetElem = document.getElementById('field-description');

	customSelectElem = document.getElementById('tt_custom_select');
	sourceElem = document.getElementById('tt_custom_' + customSelectElem.selectedIndex);

	if (!sourceElem.value)
	{
		return
	}

	if (evt.type == "change")
	{
		answer = confirm("用自定义模板的内容替换描述文字吗?");
		if (!answer)
		{
			return;
		}
	}

	// update description textarea
	targetElem.value = sourceElem.value ? sourceElem.value : "";

}

function onCustomSave(evt) {
	sourceElem = document.getElementById('field-description');
	targetElem = document.getElementById('tt_custom_textarea');
	if (!targetElem)
	{
		return
	}


	customNameElem = document.getElementById('tt_custom_name');
	customName = prompt("请输入模板名称");
	if (customName)
	{
		customNameElem.value = customName;
	}


	// update tt_custom_textarea
	targetElem.value = sourceElem.value;

}

//// add event listener
addEvent(document.getElementById('field-type'), 'change', onTypeChanged);
addEvent(window, 'load', onTypeChanged);

addEvent(document.getElementById('tt_custom_save'), 'click', onCustomSave);

addEvent(document.getElementById('tt_custom_select'), 'change', onCustomChanged);

// set focus
summary = document.getElementById('field-summary');
if (summary)
{
	summary.focus();
}


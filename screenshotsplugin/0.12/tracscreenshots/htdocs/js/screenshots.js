function checkAll(name, check)
{
  var checkboxes = document.getElementsByName(name);
  for (var I = 0; I < checkboxes.length; ++I)
  {
    checkboxes[I].checked = check;
  }
}

function checkNumber(evt)
{
  var keycode;

  if (evt)
    ;
  else if (window.event)
    evt = window.event;
  else if (event)
    evt = event;
  else
    return true;

  if (evt.charCode)
    keycode = evt.charCode;
  else if (evt.keyCode)
    keycode = evt.keyCode;
  else if (evt.which)
    keycode = evt.which;
  else
    keycode = 0;

  return ((keycode >= 48 && keycode <= 57) || (keycode == 8) ||
   (keycode == 46) || (keycode >= 33 && keycode <= 40));
}

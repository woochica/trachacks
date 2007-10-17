function check_all(name, check)
{
  var checkboxes = document.getElementsByName(name);
  for (var I = 0; I < checkboxes.length; ++I)
  {
    checkboxes[I].checked = check;
  }
}

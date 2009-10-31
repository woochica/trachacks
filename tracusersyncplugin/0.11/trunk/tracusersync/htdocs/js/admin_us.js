function check_alert(elem) {
  if (elem.checked) {
    elem.parentNode.setAttribute('class','us_alert');
  } else {
    elem.parentNode.setAttribute('class','us_noalert');
  }
}
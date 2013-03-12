function exclude(policy, excludedfields) {

  if (condition(policy)) {
    for (var i = 0; i != excludedfields.length; i++) {
      $("#field-" + excludedfields[i]).hide();
    }
  }
  else {
    for (var i = 0; i != excludedfields.length; i++) {
      $("#field-" + excludedfields[i]).show();
    }
  }

}

function excludeSubmit(policy, excludedfields) {

  if (condition(policy)) {
    for (var i = 0; i != excludedfields.length; i++) {
      ("#field-" + excludedfields[i]).val("");
    }
  }

  return true;
}
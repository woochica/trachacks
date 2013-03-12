function requires(policy, requiredfields) {
  var missing = [];
  if (condition(policy)) {
    for (var i = 0; i != requiredfields.length; i++) {
      var field = $("#field-" + requiredfields[i]).val();
      if (!field) {
        missing.push(requiredfields[i]);
      }
    }

    if (missing.length != 0) {

      if (missing.length == 1) {
        prestring = missing[0] + " is a required field ";
        poststring = "Please provide this value.";
      }
      else {
        prestring = missing.join(", ") + " are required fields ";
        poststring = "Please provide these values.";
      }

      return prestring + "for tickets where " + policytostring(policy) + ".\n" + poststring;
    }
  }
  return true;
}

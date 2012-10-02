
function showModForm(trac_username, st_username, default_cc, report) {
  
  /*
   * Find the form
   */
  mod = document.getElementById('moddiv');
  if (mod == null) {
    alert('Form not found');
    return;
  }

  /*
   * If the form's already visible, toggle the visibility and we're done.
   */
  if (mod.style.display == "inline") {
    mod.style.display = "none";
    return;
  }

  /*
   * Display the form.
   */
  mod.style.display = "inline";

  /*
   * Fill in the form.
   */
  field = document.getElementById('mod_orig_username');
  if (field) {
    field.value = trac_username;
  }

  field = document.getElementById('mod_trac_username');
  if (field) {
    field.value = trac_username;
  }

  field = document.getElementById('mod_st_username');
  if (field) {
    field.value = st_username;
  }

  field = document.getElementById('mod_st_password');
  if (field) {
    field.value = '__as_before__';
  }

  field = document.getElementById('mod_default_cc');
  if (field) {
    field.checked = default_cc;
  }

  field = document.getElementById('mod_report');
  if (field) {
    field.checked = report;
  }

  /*
   * Update fieldset caption
   */
  updateCaption();
}

function hideModForm() {
  
  /*
   * Find the form
   */
  mod = document.getElementById('moddiv');
  if (mod) {
    mod.style.display = 'none';
  }
}

function updateCaption() {

  field = document.getElementById('mod_trac_username');
  if (!field)
    return;

  username = field.value;
  
  legend = document.getElementById('mod_legend')
  if (legend) {
    legend.innerHTML = username;
  }
}


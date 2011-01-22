/* AJAX function that changes value of attribute <name> of item with id <id> to
value <value>. <url> is URL of AJAX request handler. */
function change_attribute(url, name, value)
{
  function callback(data, text_status)
  {
    // Nothing.
  };

  arguments = {'discussion_action' : 'edit-attribute',
    'name' : name,
    'value' : value,
    '__FORM_TOKEN': $('input[name="__FORM_TOKEN"]')[0].value};

  $.post(url, arguments, callback);
}

function subscription_select(authname, subscribe)
{
  $("select#subscribers option[value='" + authname + "']").attr("selected",
    subscribe ? "selected" : "");
}

function subscribe_user(url, authname, subscribe)
{
  function callback(data, text_status)
  {
    // Nothing.
  }

  arguments = {'discussion_action' : subscribe ? 'subscribe' : 'unsubscribe',
    '__FORM_TOKEN': $('input[name="__FORM_TOKEN"]')[0].value};
  $.post(url, arguments, callback);
  $("select#subscribers option[value='" + authname + "']").attr("selected",
    subscribe ? "selected" : "");
}

/* Hides/reveals all "Reply" and "Quote" links on page when topic is
locked/unlcoked */
function lock_topic(value)
{
  $("a.reply, a.quote").css("display", value ? "none" : "");
}

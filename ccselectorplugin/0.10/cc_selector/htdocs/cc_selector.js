// populate the list of default developers that should always be there
// It probably must come from database, but I'm too lazy - vnaum
function get_default_devs()
{
  var retval = new Object;
  var devs = new Array (
    'developer1',
    'developer2',
    'vladislav.naumov@gmail.com'
  );
  for (var i in devs)
  {
    retval[devs[i]] = false;  // start as unchecked
  }
  return retval;
}

// this function shows selection pop-up
function show_selection(e)
{
  thisurl = document.location.href;
  
  nurl = thisurl.split('/');
  if ( nurl.pop() != 'newticket')
  {
    // remove one more component, unless we're doing "new ticket"
    nurl.pop();
  }
  nurl = nurl.join('/');
  nurl = nurl + "/chrome/cc_selector/cc_selector.html";

  // MSIE crutch
  if ( ! e )
  {
    e = event
  }

  window.open(nurl,
    "cc_selector",
    "width=300,height=400,scrollbars=1,resizable=1,left=" + e.screenX + ",top=" + e.screenY
  );
  return;
}

// onload function. Used in both ticket window and in pop-up.
function afterLoad()
{
  after_field = "cc";
  p = document.getElementById(after_field);
  if ( ! p )  
  {
    split_into_checkboxes('cc', 'ccdiv')
    return;
  }
  
  p = p.parentNode;
  
  var ccb = document.createElement('input');
  ccb.setAttribute("type", "button");
  ccb.setAttribute("id", "ccbutton");
  ccb.setAttribute("name", "ccbutton");
  ccb.setAttribute("value", ">");
  ccb.setAttribute("alt", "Extended CC selection");
  // ccb.setAttribute("onClick", "show_selection()");
  ccb.onclick = show_selection;
  p.appendChild(ccb);
}

// split CC string into object
function split_field(fieldid)
{
  var retval = get_default_devs();

  f = document.getElementById(fieldid);
  if ( ! f )
  {
    // find parent window
    f = window.opener.document.getElementById(fieldid);
  }
  str = f.value;
  str = str.replace(/,\s*/g, ' ');
  str = str.replace(/\s+/g, ' ');
  
  var arr = str.split(' ');
 
  for (var w in arr) {
    if (arr[w].length == 0)
    {
      // skip emptys
      continue;
    }
    retval[arr[w]] = true;
  }
  return retval;
}

// checkbox onclick reaction - set CC value
function cc_toggle(name, field, ckbox) {
  params = new Array (name, field, ckbox)
  params[2] = ckbox.id;

  name = ckbox.name;
  checked = ckbox.checked;
  devs = split_field(field);
  
  devs[name] = checked;
  // generate new value

  activedevs = new Array();
  for (var d in devs) {
    if (devs[d]) {
      activedevs.push(d)
    }
  }
  newval = activedevs.join(', ');
  
  target = document.getElementById(field)
  if ( ! target )
  {
    // find target in parent window
    target = window.opener.document.getElementById(field);
  }
  target.value = newval;
}

// Fill given div with CC field contents
function split_into_checkboxes(fromid, toid) {
  t = document.getElementById(toid);
 
  devs = split_field(fromid);

  for (var w in devs) {
    v = 'cc to ' + w;
    t.appendChild(document.createElement('br'));
    
    var ck = document.createElement('input');
    ck.setAttribute("type", "checkbox");
    ck.setAttribute("id", "cc_" + w);
    ck.setAttribute("name", w);
    if (devs[w]) {
      ck.setAttribute("checked", true );
      ck.setAttribute("defaultChecked", true );
    }
    
    name = "'" + w + "'";
    field = "'" + fromid + "'";
    ckbox = "this";
    params = new Array (name, field, ckbox)
    // ck.setAttribute("onChange", "cc_toggle(" + params.join(', ') + ")");
    ck.onclick = function(){ cc_toggle(w, fromid, this); };
    
    t.appendChild(ck);
    
    t.appendChild(document.createTextNode(v));
  }
}

// utility function
function teAddEventListener(elem, evt, func, capture)
{
   capture = capture || false;
   if (elem.addEventListener) elem.addEventListener(evt, func, capture);
   else elem.attachEvent('on'+evt, func);
   return func;
}

// automatically add button on load:
teAddEventListener(window, 'load', afterLoad)

<?cs include:"header.cs" ?>
<?cs include:"macros.cs" ?>

<div id="ctxtnav" class="nav"><?cs
 if:query.report_href ?><ul>
  <li class="first"><a href="<?cs
    var:query.report_href ?>">Available Reports</a></li>
  </ul><?cs
 /if ?>
</div>

<?cs def:num_matches(v) ?><span class="numrows">(<?cs 
 alt:v ?>No<?cs /alt ?> match<?cs if:v != 1 ?>es<?cs /if ?>)</span><?cs
/def ?>

<div id="content" class="query">
 <h1><?cs var:title ?> <?cs call:num_matches(query.num_matches) ?></h1>

<form id="query" method="post" action="<?cs var:trac.href.query ?>">
 <fieldset id="filters">
  <legend>Filters</legend>
  <?cs def:checkbox_checked(constraint, option) ?><?cs
   set:checked = 0 ?><?cs
   each:value = constraint.values ?><?cs
    if:(value == option) == (constraint.mode == '') ?><?cs
      set:checked = 1 ?><?cs
    /if ?><?cs
   /each ?><?cs
   if:checked ?> checked="checked"<?cs /if ?><?cs
  /def ?>
  <table summary="Query filters">
   <tbody><tr style="height: 1px"><td colspan="4"></td></tr></tbody><?cs
   each:field = query.fields ?><?cs
   each:constraint = query.constraints ?><?cs
    if:name(field) == name(constraint) ?>
     <tbody><tr class="<?cs var:name(field) ?>">
      <th scope="row"><label><?cs var:field.label ?></label></th><?cs
      if:field.type != "radio" && field.type != "checkbox" ?>
       <td class="mode">
        <select name="<?cs var:name(field) ?>_mode"><?cs
         each:mode = query.modes[field.type] ?>
          <option value="<?cs var:mode.value ?>"<?cs
           if:mode.value == constraint.mode ?> selected="selected"<?cs
           /if ?>><?cs var:mode.name ?></option><?cs
         /each ?>
        </select>
       </td><?cs
      /if ?>
      <td class="filter"<?cs
        if:field.type == "radio" || field.type == "checkbox" ?> colspan="2"<?cs
        /if ?>><?cs
       if:field.type == "select" ?><?cs
        each:value = constraint.values ?>
         <select name="<?cs var:name(constraint) ?>"><option></option><?cs
         each:option = field.options ?>
          <option<?cs if:option == value ?> selected="selected"<?cs /if ?>><?cs
            var:option ?></option><?cs
         /each ?></select><?cs
         if:name(value) != len(constraint.values) - 1 ?>
          </td>
          <td class="actions"><input type="submit" name="rm_filter_<?cs
             var:name(field) ?>_<?cs var:name(value) ?>" value="-" /></td>
         </tr><tr class="<?cs var:name(field) ?>">
          <th colspan="2"><label>or</label></th>
          <td class="filter"><?cs
         /if ?><?cs
        /each ?><?cs
       elif:field.type == "radio" ?><?cs
        each:option = field.options ?>
         <input type="checkbox" id="<?cs var:name(field) ?>_<?cs
           var:option ?>" name="<?cs var:name(field) ?>" value="<?cs
           var:option ?>"<?cs call:checkbox_checked(constraint, option) ?> />
         <label for="<?cs var:name(field) ?>_<?cs var:option ?>"><?cs
           alt:option ?>none<?cs /alt ?></label><?cs
        /each ?><?cs
       elif:field.type == "checkbox" ?>
        <input type="radio" id="<?cs var:name(field) ?>_on" name="<?cs
          var:name(field) ?>" value="1"<?cs
          if:constraint.mode != '!' ?> checked="checked"<?cs /if ?> />
        <label for="<?cs var:name(field) ?>_on">yes</label>
        <input type="radio" id="<?cs var:name(field) ?>_off" name="<?cs
          var:name(field) ?>" value="!1"<?cs
          if:constraint.mode == '!' ?> checked="checked"<?cs /if ?> />
        <label for="<?cs var:name(field) ?>_off">no</label><?cs
       elif:field.type == "text" ?><?cs
        each:value = constraint.values ?>
        <input type="text" name="<?cs var:name(field) ?>" value="<?cs
          var:value ?>" size="42" /><?cs
         if:name(value) != len(constraint.values) - 1 ?>
          </td>
          <td class="actions"><input type="submit" name="rm_filter_<?cs
             var:name(field) ?>_<?cs var:name(value) ?>" value="-" /></td>
         </tr><tr class="<?cs var:name(field) ?>">
          <th colspan="2"><label>or</label></th>
          <td class="filter"><?cs
         /if ?><?cs
        /each ?><?cs
       /if ?>
      </td>
      <td class="actions"><input type="submit" name="rm_filter_<?cs
         var:name(field) ?><?cs
         if:field.type != 'radio' ?>_<?cs
          var:len(constraint.values) - 1 ?><?cs
         /if ?>" value="-" /></td>
     </tr></tbody><?cs /if ?><?cs
    /each ?><?cs
   /each ?>
   <tbody><tr class="actions">
    <td class="actions" colspan="4" style="text-align: right">
     <label for="add_filter">Add filter</label>&nbsp;
     <select name="add_filter" id="add_filter">
      <option></option><?cs
      each:field = query.fields ?>
       <option value="<?cs var:name(field) ?>"<?cs
         if:field.type == "radio" ?><?cs
          if:len(query.constraints[name(field)]) != 0 ?> disabled="disabled"<?cs
          /if ?><?cs
         /if ?>><?cs var:field.label ?></option><?cs
      /each ?>	
     </select>
     <input type="submit" name="add" value="+" />
    </td>
   </tr></tbody>
  </table>
 </fieldset>
 <p class="option">
  <label for="group">Group results by</label>
  <select name="group" id="group">
   <option></option><?cs
   each:field = query.fields ?><?cs
    if:field.type == 'select' || field.type == 'radio' ||
       name(field) == 'owner' ?>
     <option value="<?cs var:name(field) ?>"<?cs
       if:name(field) == query.group ?> selected="selected"<?cs /if ?>><?cs
       var:field.label ?></option><?cs
    /if ?><?cs
   /each ?>
  </select>
  <input type="checkbox" name="groupdesc" id="groupdesc"<?cs
    if:query.groupdesc ?> checked="checked"<?cs /if ?> />
  <label for="groupdesc">descending</label>
  <script type="text/javascript">
    var group = document.getElementById("group");
    var updateGroupDesc = function() {
      enableControl('groupdesc', group.selectedIndex > 0);
    }
    addEvent(window, 'load', updateGroupDesc);
    addEvent(group, 'change', updateGroupDesc);
  </script>
 </p>
 <p class="option">
  <input type="checkbox" name="verbose" id="verbose"<?cs
    if:query.verbose ?> checked="checked"<?cs /if ?> />
  <label for="verbose">Show full description under each result</label>
 </p>
 <div class="buttons">
  <input type="hidden" name="order" value="<?cs var:query.order ?>" />
  <?cs if:query.desc ?><input type="hidden" name="desc" value="1" /><?cs /if ?>
  <input type="submit" name="update" value="Update" />
 </div>
 <hr />
</form>
<script type="text/javascript"><?cs set:idx = 0 ?>
 var properties={<?cs each:field = query.fields ?><?cs
  var:name(field) ?>:{type:"<?cs var:field.type ?>",label:"<?cs
  var:field.label ?>",options:[<?cs
   each:option = field.options ?>"<?cs var:option ?>"<?cs
    if:name(option) < len(field.options) -1 ?>,<?cs /if ?><?cs
   /each ?>]}<?cs
  set:idx = idx + 1 ?><?cs if:idx < len(query.fields) ?>,<?cs /if ?><?cs
 /each ?>};<?cs set:idx = 0 ?>
 var modes = {<?cs each:type = query.modes ?><?cs var:name(type) ?>:[<?cs
  each:mode = type ?>{text:"<?cs var:mode.name ?>",value:"<?cs var:mode.value ?>"}<?cs
   if:name(mode) < len(type) -1 ?>,<?cs /if ?><?cs
  /each ?>]<?cs
  set:idx = idx + 1 ?><?cs if:idx < len(query.modes) ?>,<?cs /if ?><?cs
 /each ?>};
 initializeFilters();
</script>

<?cs def:thead() ?>
 <thead><tr><?cs each:header = query.headers ?>
  <th class="<?cs var:header.name ?><?cs if:query.order == header.name ?> <?cs
    if:query.desc ?>desc<?cs else ?>asc<?cs /if ?><?cs /if ?>">
   <a title="Sort by <?cs var:header.label ?><?cs
     if:query.order == header.name && !query.desc ?> (descending)<?cs
     /if ?>" href="<?cs var:header.href ?>"><?cs var:header.label ?></a>
  </th><?cs
 /each ?></tr></thead>
<?cs /def ?>

<?cs if:len(query.results) ?><?cs
 if:!query.group ?>
  <table class="listing tickets">
  <?cs call:thead() ?><tbody><?cs
 /if ?><?cs
 each:result = query.results ?><?cs
  if:result[query.group] != prev_group ?>
   <?cs if:prev_group ?></tbody></table><?cs /if ?>
   <h2><?cs
    each:field = query.fields ?><?cs
     if:name(field) == query.group ?><?cs
      var:field.label ?><?cs
     /if ?><?cs
    /each ?>: <?cs var:result[query.group] ?> <?cs call:num_matches(query.num_matches_group[result[query.group]]) ?></h2>
   <table class="listing tickets">
   <?cs call:thead() ?><tbody><?cs
  /if ?>
  <tr class="<?cs
   if:name(result) % 2 ?>odd<?cs else ?>even<?cs /if ?> prio<?cs
   var:result.priority_value ?><?cs
   if:result.added ?> added<?cs /if ?><?cs
   if:result.changed ?> changed<?cs /if ?><?cs
   if:result.removed ?> removed<?cs /if ?>"><?cs
  each:header = query.headers ?><?cs
   if:name(header) == 0 ?><td class="id"><a href="<?cs
    var:result.href ?>" title="View ticket"><?cs var:result.id ?></a></td><?cs
   else ?><td class="<?cs var:header.name ?>"><?cs
     if:header.name == 'summary' ?><a href="<?cs
      var:result.href ?>" title="View ticket"><?cs
      var:result.summary ?></a><?cs
     else ?><span><?cs var:result[header.name] ?></span><?cs
     /if ?></td><?cs
   /if ?><?cs
  /each ?>
  <?cs if:query.verbose ?>
   </tr><tr class="fullrow"><td colspan="<?cs var:len(query.headers) ?>">
    <p class="meta">Reported by <strong><?cs var:result.reporter ?></strong>,
    <?cs var:result.time ?><?cs if:result.description ?>:<?cs /if ?></p>
    <?cs if:result.description ?><p><?cs var:result.description ?></p><?cs /if ?>
   </td>
  <?cs /if ?><?cs set:prev_group = result[query.group] ?>
 </tr><?cs /each ?>
</tbody></table><?cs
/if ?>


<?cs if:trac.acl.TICKET_BATCH_MODIFY ?>

<br/>
<form id="batchmod" method="post" action="<?cs var:trac.href.query ?>">
<fieldset id="properties">
<legend>Batch Modify Properties</legend>

  <table>
    <tr>
        <th style="text-align: left">
            <input type="checkbox" id="bm_comment" name="bm_comment" />
            <label for="comment">Comment:</label>
        </th>
        <td class="fullrow" colspan="3">
         <input type="text" id="comment" name="comment" value="<?cs
         var:ticket.summary ?>" size="70" disabled="true"/>
        </td>
        <script type="text/javascript">
            var bm_comment = document.getElementById("bm_comment");
            var comment = document.getElementById("comment");
            var updateComment = function() {
                enableControl('comment', bm_comment.checked);
            }
            addEvent(window, 'load', updateComment);
            addEvent(bm_comment, 'change', updateComment);
        </script>
    </tr>

  <tr><?cs set:num_fields = 0 ?><?cs
  each:field = ticket.fields ?><?cs
   if:!field.skip ?><?cs
    set:num_fields = num_fields + 1 ?><?cs
   /if ?><?cs
  /each ?><?cs set:idx = 0 ?><?cs
   each:field = ticket.fields ?><?cs
    if:!field.skip ?>


   <?cs set:fullrow = field.type == 'textarea' ?><?cs
     if:fullrow && idx % 2 ?><?cs set:idx = idx + 1 ?><th class="col2"></th><td></td></tr><tr><?cs /if ?>

    <th class="col<?cs var:idx % 2 + 1 ?>" style="text-align: left">
    <?cs if:field.type != 'radio' ?>
        <input type="checkbox" id="bm_<?cs var:name(field) ?>" name="bm_<?cs var:name(field) ?>" />
        <label for="<?cs var:name(field) ?>">
        <script type="text/javascript">
            var bm_<?cs var:name(field) ?> = document.getElementById("bm_<?cs var:name(field) ?>");
            var ctrl_<?cs var:name(field) ?> = document.getElementById("<?cs var:name(field) ?>");
            var update<?cs var:name(field) ?>  = function() {
                enableControl('<?cs var:name(field) ?>', bm_<?cs var:name(field) ?>.checked);
            }
            addEvent(window, 'load', update<?cs var:name(field) ?>);
            addEvent(bm_<?cs var:name(field) ?>, 'change', update<?cs var:name(field) ?>);
        </script>
    <?cs /if ?>
    <?cs alt:field.label ?>
        <input type="checkbox" id="bm_<?cs var:field.name ?>" name="bm_<?cs var:field.name ?>" />
        <?cs var:field.name ?>
        <script type="text/javascript">
            var bm_<?cs var:field.name ?> = document.getElementById("bm_<?cs var:field.name ?>");
            var ctrl_<?cs var:field.name ?> = document.getElementById("<?cs var:field.name ?>");
            var update<?cs var:field.name ?>  = function() {
                enableControl('<?cs var:field.name ?>', bm_<?cs var:field.name ?>.checked);
            }
            addEvent(window, 'load', update<?cs var:field.name ?>);
            addEvent(bm_<?cs var:field.name ?>, 'change', update<?cs var:field.name ?>);
        </script>
    <?cs /alt ?>:
    <?cs if:field.type != 'radio' ?></label><?cs /if ?>
    </th>


     <td<?cs if:fullrow ?> colspan="3"<?cs /if ?>><?cs
      if:field.type == 'text' ?><input type="text" id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" value="<?cs var:ticket[name(field)] ?>" disabled="true" /><?cs
      elif:field.type == 'select' ?>
        <select id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" enabled="false"><?cs
        if:field.optional ?><option></option><?cs /if ?><?cs
        each:option = field.options ?><option<?cs
         if:option == ticket[name(field)] ?> selected="selected"<?cs /if ?>><?cs
         var:option ?></option><?cs
        /each ?></select><?cs
      elif:field.type == 'checkbox' ?><input type="hidden" name="checkbox_<?cs
        var:name(field) ?>" /><input type="checkbox" id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>" value="1"<?cs
        if:ticket[name(field)] ?> checked="checked"<?cs /if ?> disabled="true" /><?cs
      elif:field.type == 'textarea' ?><textarea id="<?cs
        var:name(field) ?>" name="<?cs
        var:name(field) ?>"<?cs
        if:field.height ?> rows="<?cs var:field.height ?>"<?cs /if ?><?cs
        if:field.width ?> cols="<?cs var:field.width ?>"<?cs /if ?> disabled="true" >
<?cs var:ticket[name(field)] ?></textarea><?cs
      elif:field.type == 'radio' ?><?cs set:optidx = 0 ?><?cs
       each:option = field.options ?><label><input type="radio" id="<?cs
         var:name(field) ?>" name="<?cs
         var:name(field) ?>" value="<?cs var:option ?>"<?cs
         if:ticket[name(field)] == option ?> checked="checked"<?cs /if ?> disabled="true"/> <?cs
         var:option ?></label> <?cs set:optidx = optidx + 1 ?><?cs
        /each ?><?cs
      /if ?></td><?cs
     if:idx % 2 || fullrow ?><?cs
      if:idx < num_fields - 1 ?></tr><tr><?cs
      /if ?><?cs
     elif:idx == num_fields - 1 ?><th class="col2"></th><td></td><?cs
     /if ?><?cs set:idx = idx + #fullrow + 1 ?><?cs
    /if ?><?cs
   /each ?></tr>

  </table>
</fieldset>

<input type="submit" name="batchmod" value="Batch Modify" />
</form>
<?cs /if ?>

<div id="help">
 <strong>Note:</strong> See <a href="<?cs var:trac.href.wiki ?>/TracQuery">TracQuery</a> 
 for help on using queries.
</div>

</div>
<?cs include:"footer.cs" ?>

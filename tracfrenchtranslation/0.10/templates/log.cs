<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <ul>
  <li class="last">
   <a href="<?cs var:log.browser_href ?>">Voir la dernière révision</a>
  </li><?cs
  if:len(chrome.links.prev) ?>
   <li class="first<?cs if:!len(chrome.links.next) ?> last<?cs /if ?>">
    &larr; <a href="<?cs var:chrome.links.prev.0.href ?>" title="<?cs
      var:chrome.links.prev.0.title ?>">Révisions postérieures</a>
   </li><?cs
  /if ?><?cs
  if:len(chrome.links.next) ?>
   <li class="<?cs if:!len(chrome.links.prev) ?>first <?cs /if ?>last">
    <a href="<?cs var:chrome.links.next.0.href ?>" title="<?cs
      var:chrome.links.next.0.title ?>">Révisions antérieures</a> &rarr;
   </li><?cs
  /if ?>
 </ul>
</div>


<div id="content" class="log">
 <h1><?cs call:browser_path_links(log.path, log) ?></h1>
 <form id="prefs" action="<?cs var:browser_current_href ?>" method="get">
  <div>
   <input type="hidden" name="action" value="<?cs var:log.mode ?>" />
   <label>Voir le journal du dépôt à partir de <input type="text" id="rev" name="rev" value="<?cs
    var:log.items.0.rev ?>" size="5" /></label><br/>
   <label>et jusqu'à <input type="text" id="stop_rev" name="stop_rev" value="<?cs
    var:log.stop_rev ?>" size="5" />révisions précédentes</label>
   <br />
   <div class="choice">
    <fieldset>
     <legend>Mode:</legend>
     <label for="stop_on_copy">
      <input type="radio" id="stop_on_copy" name="mode" value="stop_on_copy" <?cs
       if:log.mode != "follow_copy" || log.mode != "path_history" ?> checked="checked" <?cs
       /if ?> />
      Arrêt sur copie 
     </label>
     <label for="follow_copy">
      <input type="radio" id="follow_copy" name="mode" value="follow_copy" <?cs
       if:log.mode == "follow_copy" ?> checked="checked" <?cs /if ?> />
      Suivi des copies
     </label>
     <label for="path_history">
      <input type="radio" id="path_history" name="mode" value="path_history" <?cs
       if:log.mode == "path_history" ?> checked="checked" <?cs /if ?> />
      Ajouts, déplacements et suppression uniquement
     </label>
    </fieldset>
   </div>
   <label><input type="checkbox" name="verbose" <?cs
    if:log.verbose ?> checked="checked" <?cs
    /if ?> /> Voir le journal complet</label>
  </div>
  <div class="buttons">
   <input type="submit" value="Actualiser" 
          title="Note: En actualisant, l'historique de la page est remis à zero" />
  </div>
 </form>

 <div class="diff">
  <div id="legend">
   <h3>Legend:</h3>
   <dl>
    <dt class="add"></dt><dd>Ajouté</dd><?cs
    if:log.mode == "path_history" ?>
     <dt class="rem"></dt><dd>Supprimé</dd><?cs
    /if ?>
    <dt class="mod"></dt><dd>Modifié</dd>
    <dt class="cp"></dt><dd>Copié ou renommé</dd>
   </dl>
  </div>
 </div>

 <form action="<?cs var:log.changeset_href ?>" method="get">
  <div class="buttons"><input type="submit" value="Voir les modifications" 
       title="Différences entre ancienne et nouvelle révision (sélectionnez-les en dessous)" />
 </div>
 <table id="chglist" class="listing">
  <thead>
   <tr>
    <th class="diff"></th>
    <th class="change"></th>
    <th class="data">Date</th>
    <th class="rev">Rév.</th>
    <th class="chgset">Version</th>
    <th class="author">Auteur</th>
    <th class="summary">Description</th>
   </tr>
  </thead>
  <tbody><?cs
   set:indent = #1 ?><?cs
   set:idx = #0 ?><?cs
   each:item = log.items ?><?cs
    if:item.copyfrom_path ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="copyfrom_path" colspan="8" style="padding-left: <?cs var:indent ?>em">
       copié depuis <a href="<?cs var:item.browser_href ?>"?><?cs var:item.copyfrom_path ?></a>:
      </td>
     </tr><?cs
     set:indent = indent + #1 ?><?cs
    elif:log.mode == "path_history" ?><?cs
      set:indent = #1 ?><?cs
    /if ?>
    <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
     <td class="diff">
      <input type="radio" name="old" 
             value="<?cs var:item.path ?>@<?cs var:item.rev ?>" <?cs
          if:idx == #1 ?> checked="checked" <?cs /if ?> />
      <input type="radio" name="new" 
             value="<?cs var:item.path ?>@<?cs var:item.rev ?>" <?cs
          if:idx == #0 ?> checked="checked" <?cs /if ?> /></td>
     <td class="change" style="padding-left:<?cs var:indent ?>em">
      <a title="Voir le journal en commencant à partir de la révision" href="<?cs var:item.log_href ?>">
       <span class="<?cs var:item.change ?>"></span>
       <span class="comment">(<?cs var:item.change ?>)</span>
      </a>
     </td>
     <td class="date"><?cs var:log.changes[item.rev].date ?></td>
     <td class="rev">
      <a href="<?cs var:item.browser_href ?>" 
         title="Consultez la révision <?cs var:item.rev ?>">@<?cs var:item.rev ?></a>
     </td>
     <td class="chgset">
      <a href="<?cs var:item.changeset_href ?>"
         title="Voir la version [<?cs var:item.rev ?>]">[<?cs var:item.rev ?>]</a>
     </td>
     <td class="author"><?cs var:log.changes[item.rev].author ?></td>
     <td class="summary"><?cs var:log.changes[item.rev].message ?></td>
    </tr><?cs
    set:idx = idx + 1 ?><?cs
   /each ?>
  </tbody>
 </table><?cs
 if:len(log.items) > #10 ?>
  <div class="buttons"><input type="submit" value="View changes" 
       title="Différences entre ancienne et nouvelle révision (sélectionnez-les en dessous)" />
  </div><?cs
 /if ?>
 </form><?cs
 if:len(links.prev) || len(links.next) ?><div id="paging" class="nav"><ul><?cs
  if:len(links.prev) ?><li class="first<?cs
   if:!len(links.next) ?> last<?cs /if ?>">&larr; <a href="<?cs
   var:links.prev.0.href ?>" title="<?cs
   var:links.prev.0.title ?>">Révisions postérieures</a></li><?cs
  /if ?><?cs
  if:len(links.next) ?><li class="<?cs
   if:len(links.prev) ?>first <?cs /if ?>last"><a href="<?cs
   var:links.next.0.href ?>" title="<?cs
   var:links.next.0.title ?>">Révisions antérieures</a> &rarr;</li><?cs
  /if ?></ul></div><?cs
 /if ?>

 <div id="help">
  <strong>Note:</strong> See <a href="<?cs var:trac.href.wiki
  ?>/TracRevisionLog">TracRevisionLog</a> for help on using the revision log.
 </div>

</div>
<?cs include "footer.cs"?>

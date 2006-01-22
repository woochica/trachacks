<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <h2>Navigation</h2><?cs
 with:links = chrome.links ?>
  <ul><?cs
   if:changeset.chgset ?><?cs
    if:changeset.restricted ?><?cs
     set:change = "Change" ?><?cs
    else ?><?cs 
     set:change = "Changeset" ?><?cs
    /if ?>
    <li class="first"><?cs
     if:len(links.prev) ?> &larr; 
      <a class="prev" href="<?cs var:links.prev.0.href ?>" title="<?cs
        var:links.prev.0.title ?>"><?cs alt:translation[change] ?><?cs 
        var:change ?><?cs /alt?> précédente</a> <?cs 
     else ?>
      <span class="missing">&larr; <?cs alt:translation[change] ?><?cs 
        var:change ?><?cs /alt?> précédente</span><?cs 
     /if ?>
    </li>
    <li class="last"><?cs
     if:len(links.next) ?>
      <a class="next" href="<?cs var:links.next.0.href ?>" title="<?cs
       var:links.next.0.title ?>"><?cs alt:translation[change] ?><?cs 
        var:change ?><?cs /alt?> suivante</a> &rarr; <?cs 
     else ?>
      <span class="missing"><?cs alt:translation[change] ?><?cs 
        var:change ?><?cs /alt?> suivante &rarr;</span><?cs
     /if ?>
    </li><?cs
   else ?>
    <li class="first"><a href="<?cs var:changeset.reverse_href ?>">Diff inverse</a></li><?cs
   /if ?>
  </ul><?cs
 /with ?>
</div>

<div id="content" class="changeset">
 <div id="title"><?cs
  if:changeset.chgset ?><?cs
   if:changeset.restricted ?>
    <h1>Version <a title="Afficher l'ensemble des changements" href="<?cs var:changeset.href.new_rev ?>">
      <?cs var:changeset.new_rev ?></a> 
     pour <a title="Afficher l'élément dans le navigateur" href="<?cs var:changeset.href.new_path ?>">
      <?cs var:changeset.new_path ?></a> 
    </h1><?cs
   else ?>
    <h1>Changeset <?cs var:changeset.new_rev ?></h1><?cs
   /if ?><?cs
  else ?><?cs
    if:changeset.restricted ?>
    <h1>Modifications dans <a title="Afficher l'élément dans le navigateur" href="<?cs var:changeset.href.new_path ?>">
      <?cs var:changeset.new_path ?></a>
      <a title="Afficher le journal des révisions" href="<?cs var:changeset.href.log ?>">
      [<?cs var:changeset.old_rev ?>:<?cs var:changeset.new_rev ?>]</a>
    </h1><?cs
   else ?>
    <h1>Modification de <a title="Show entry in browser" href="<?cs var:changeset.href.old_path ?>">
      <?cs var:changeset.old_path ?></a> 
     à <a title="Afficher l'ensemble des changements" href="<?cs var:changeset.href.old_rev ?>">
      r<?cs var:changeset.old_rev ?></a>
     vers <a title="Afficher l'élément dans le navigateur" href="<?cs var:changeset.href.new_path ?>">
     <?cs var:changeset.new_path ?></a> 
     à <a title="Afficher l'ensemble des changements" href="<?cs var:changeset.href.new_rev ?>">
     r<?cs var:changeset.new_rev ?></a>
    </h1><?cs
   /if ?><?cs
  /if ?>
 </div>

<?cs each:change = changeset.changes ?><?cs
 if:len(change.diff) ?><?cs
  set:has_diffs = 1 ?><?cs
 /if ?><?cs
/each ?><?cs if:has_diffs || diff.options.ignoreblanklines 
  || diff.options.ignorecase || diff.options.ignorewhitespace ?>
<form method="post" id="prefs" action="">
 <div><?cs 
  if:!changeset.chgset ?>
   <input type="hidden" name="old_path" value="<?cs var:changeset.old_path ?>" />
   <input type="hidden" name="path" value="<?cs var:changeset.new_path ?>" />
   <input type="hidden" name="old" value="<?cs var:changeset.old_rev ?>" />
   <input type="hidden" name="new" value="<?cs var:changeset.new_rev ?>" /><?cs
  /if ?>
  <label for="style">Voir les différences</label>
  <select id="style" name="style">
   <option value="inline"<?cs
     if:diff.style == 'inline' ?> selected="selected"<?cs
     /if ?>>au fil</option>
   <option value="sidebyside"<?cs
     if:diff.style == 'sidebyside' ?> selected="selected"<?cs
     /if ?>>côte à côte</option>
  </select>
  <div class="field">
   Montrer <input type="text" name="contextlines" id="contextlines" size="2"
     maxlength="3" value="<?cs var:diff.options.contextlines ?>" />
   <label for="contextlines">Lignes encadrant chaque changement</label>
  </div>
  <fieldset id="ignore">
   <legend>Ignorer:</legend>
   <div class="field">
    <input type="checkbox" id="blanklines" name="ignoreblanklines"<?cs
      if:diff.options.ignoreblanklines ?> checked="checked"<?cs /if ?> />
    <label for="blanklines">Lignes vides</label>
   </div>
   <div class="field">
    <input type="checkbox" id="case" name="ignorecase"<?cs
      if:diff.options.ignorecase ?> checked="checked"<?cs /if ?> />
    <label for="case">Changements majuscules/minuscules</label>
   </div>
   <div class="field">
    <input type="checkbox" id="whitespace" name="ignorewhitespace"<?cs
      if:diff.options.ignorewhitespace ?> checked="checked"<?cs /if ?> />
    <label for="whitespace">Changements d'espacement</label>
   </div>
  </fieldset>
  <div class="buttons">
   <input type="submit" name="update" value="Actualiser" />
  </div>
 </div>
</form><?cs /if ?>

<?cs def:node_change(item,cl,kind) ?><?cs 
  set:ndiffs = len(item.diff) ?><?cs
  set:nprops = len(item.props) ?>
  <div class="<?cs var:cl ?>"></div><?cs 
  if:cl == "rem" ?>
   <a title="Montrer ce qui a été supprimé (rev. <?cs var:item.rev.old ?>)" href="<?cs
     var:item.browser_href.old ?>"><?cs var:item.path.old ?></a><?cs
  else ?>
   <a title="Montrer l'élément dans le navigateur" href="<?cs
     var:item.browser_href.new ?>"><?cs var:item.path.new ?></a><?cs
  /if ?>
  <span class="comment">(<?cs var:kind ?>)</span><?cs
  if:item.path.old && item.change == 'copy' || item.change == 'move' ?>
   <small><em>(<?cs var:kind ?> depuis <a href="<?cs
    var:item.browser_href.old ?>" title="Montrer le fichier original (rév. <?cs
    var:item.rev.old ?>)"><?cs var:item.path.old ?></a>)</em></small><?cs
  /if ?><?cs
  if:$ndiffs + $nprops > #0 ?>
    (<a href="#file<?cs var:name(item) ?>" title="Voir les différences"><?cs
      if:$ndiffs > #0 ?><?cs var:ndiffs ?>&nbsp;diff<?cs if:$ndiffs > #1 ?>s<?cs /if ?><?cs 
      /if ?><?cs
      if:$ndiffs && $nprops ?>, <?cs /if ?><?cs 
      if:$nprops > #0 ?><?cs var:nprops ?>&nbsp;prop<?cs if:$nprops > #1 ?>s<?cs /if ?><?cs
      /if ?></a>)<?cs
  elif:cl == "mod" ?>
    (<a href="<?cs var:item.browser_href.old ?>"
        title="Voir les versions antérieures dans le navigateur">précédent</a>)<?cs
  /if ?>
<?cs /def ?>

<dl id="overview"><?cs
 if:changeset.chgset ?>
 <dt class="time">Date:</dt>
 <dd class="time"><?cs var:changeset.time ?> 
  (<?cs alt:changeset.age ?>moins d'une heure<?cs /alt ?> auparavant)</dd>
 <dt class="author">Auteur:</dt>
 <dd class="author"><?cs var:changeset.author ?></dd>
 <dt class="message">Message:</dt>
 <dd class="message" id="searchable"><?cs
  alt:changeset.message ?>&nbsp;<?cs /alt ?></dd><?cs
 /if ?>
 <dt class="files"><?cs 
  if:len(changeset.changes) > #0 ?>
   Fichiers:<?cs
  else ?>
   (Pas de fichier)<?cs
  /if ?>
 </dt>
 <dd class="files">
  <ul><?cs each:item = changeset.changes ?>
   <li><?cs
    if:item.change == 'add' ?><?cs
     call:node_change(item, 'add', 'ajouté') ?><?cs
    elif:item.change == 'delete' ?><?cs
     call:node_change(item, 'rem', 'supprimé') ?><?cs
    elif:item.change == 'copy' ?><?cs
     call:node_change(item, 'cp', 'copié') ?><?cs
    elif:item.change == 'move' ?><?cs
     call:node_change(item, 'mv', 'déplacé') ?><?cs
    elif:item.change == 'edit' ?><?cs
     call:node_change(item, 'mod', 'modifié') ?><?cs
    /if ?>
   </li>
  <?cs /each ?></ul>
 </dd>
</dl>

<div class="diff">
 <div id="legend">
  <h3>Légende:</h3>
  <dl>
   <dt class="unmod"></dt><dd>Non modifié</dd>
   <dt class="add"></dt><dd>Ajouté</dd>
   <dt class="rem"></dt><dd>Supprimé</dd>
   <dt class="mod"></dt><dd>Modifié</dd>
   <dt class="cp"></dt><dd>Copié</dd>
   <dt class="mv"></dt><dd>Déplacé</dd>
  </dl>
 </div>
 <ul class="entries"><?cs
 each:item = changeset.changes ?><?cs
  if:len(item.diff) || len(item.props) ?><li class="entry" id="file<?cs
   var:name(item) ?>"><h2><a href="<?cs
   var:item.browser_href.new ?>" title="Voir la nouvelle révision <?cs
   var:item.rev.new ?> de ce fichier dans le navigateur"><?cs
   var:item.path.new ?></a></h2><?cs
   if:len(item.props) ?><ul class="props"><?cs
    each:prop = item.props ?><li>Propriété <strong><?cs
     var:name(prop) ?></strong> <?cs
     if:prop.old && prop.new ?>modifiée de <?cs
     elif:!prop.old ?>définie<?cs
     else ?>supprimée<?cs
     /if ?><?cs
     if:prop.old && prop.new ?><em><tt><?cs var:prop.old ?></tt></em><?cs /if ?><?cs
     if:prop.new ?> à <em><tt><?cs var:prop.new ?></tt></em><?cs /if ?></li><?cs
    /each ?></ul><?cs
   /if ?><?cs
   if:len(item.diff) ?><table class="<?cs
    var:diff.style ?>" summary="Différences" cellspacing="0"><?cs
    if:diff.style == 'sidebyside' ?>
     <colgroup class="l"><col class="lineno" /><col class="content" /></colgroup>
     <colgroup class="r"><col class="lineno" /><col class="content" /></colgroup>
     <thead><tr>
      <th colspan="2"><a href="<?cs
       var:item.browser_href.old ?>" title="Voir ancienne rév. <?cs
       var:item.rev.old ?> de <?cs var:item.path.old ?>">Révision <?cs
       var:item.rev.old ?></a></th>
      <th colspan="2"><a href="<?cs
       var:item.browser_href.new ?>" title="Voir nouvelle rév. <?cs
       var:item.rev.new ?> de <?cs var:item.path.new ?>">Révision <?cs
       var:item.rev.new ?></a></th>
      </tr>
     </thead><?cs
     each:change = item.diff ?><tbody><?cs
      call:diff_display(change, diff.style) ?></tbody><?cs
      if:name(change) < len(item.diff) - 1 ?><tbody class="skipped"><tr>
       <th>&hellip;</th><td>&nbsp;</td><th>&hellip;</th><td>&nbsp;</td>
      </tr></tbody><?cs /if ?><?cs
     /each ?><?cs
    else ?>
     <colgroup><col class="lineno" /><col class="lineno" /><col class="content" /></colgroup>
     <thead><tr>
      <th title="Révision <?cs var:item.rev.old ?>"><a href="<?cs
       var:item.browser_href.old ?>" title="Voir l'ancienne révision de <?cs
       var:item.path.old ?>">r<?cs var:item.rev.old ?></a></th>
      <th title="Révision <?cs var:item.rev.new ?>"><a href="<?cs
       var:item.browser_href.new ?>" title="Voir la nouvelle révision de <?cs
       var:item.path.new ?>">r<?cs var:item.rev.new ?></a></th>
      <th>&nbsp;</th></tr>
     </thead><?cs
     each:change = item.diff ?><?cs
      call:diff_display(change, diff.style) ?><?cs
      if:name(change) < len(item.diff) - 1 ?><tbody class="skipped"><tr>
       <th>&hellip;</th><th>&hellip;</th><td>&nbsp;</td>
      </tr></tbody><?cs /if ?><?cs
     /each ?><?cs
    /if ?></table><?cs
   /if ?></li><?cs
  /if ?><?cs
 /each ?></ul>
</div>

</div>
<?cs include "footer.cs"?>

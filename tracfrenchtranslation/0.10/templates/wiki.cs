<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
 <h2>Consultation Wiki</h2>
 <ul><?cs
  if:wiki.action == "diff" ?>
   <li class="first"><?cs
     if:len(chrome.links.prev) ?> &larr; 
      <a class="prev" href="<?cs var:chrome.links.prev.0.href ?>" title="<?cs
       var:chrome.links.prev.0.title ?>">Modification précédente</a><?cs
     else ?>
      <span class="missing">&larr; Modification précédente</span><?cs
     /if ?>
   </li>
   <li><a href="<?cs var:wiki.history_href ?>">Historique</a></li>
   <li class="last"><?cs
     if:len(chrome.links.next) ?>
      <a class="next" href="<?cs var:chrome.links.next.0.href ?>" title="<?cs
       var:chrome.links.next.0.title ?>">Modification suivante</a> &rarr; <?cs
     else ?>
      <span class="missing">Modification suivante &rarr;</span><?cs
     /if ?>
   </li><?cs
  elif:wiki.action == "history" ?>
   <li class="last"><a href="<?cs var:wiki.current_href ?>">Version actuelle</a></li><?cs
  else ?>
   <li><a href="<?cs var:trac.href.wiki ?>">Page d'accueil</a></li>
   <li><a href="<?cs var:trac.href.wiki ?>/TitleIndex">Sommaire</a></li>
   <li><a href="<?cs var:trac.href.wiki ?>/RecentChanges">Modif. récentes</a></li>
   <li class="last"><a href="<?cs var:wiki.last_change_href ?>">Dernière modif.</a></li><?cs 
  /if ?>
 </ul>
 <hr />
</div>

<div id="content" class="wiki">

 <?cs if wiki.action == "delete" ?><?cs 
  if:wiki.version - wiki.old_version > 1 ?><?cs
   set:first_version = wiki.old_version + 1 ?><?cs
   set:version_range = "les versions "+first_version+" à "+wiki.version+" de " ?><?cs
   set:delete_what = "ces versions" ?><?cs
  elif:wiki.version ?><?cs
   set:version_range = "la version "+wiki.version+" de " ?><?cs
   set:delete_what = "cette version" ?><?cs
  else ?><?cs
   set:version_range = "" ?><?cs
   set:delete_what = "page" ?><?cs
  /if ?>
  <h1>Supprimer <?cs var:version_range ?><a href="<?cs
    var:wiki.current_href ?>"><?cs var:wiki.page_name ?></a></h1>
  <form action="<?cs var:wiki.current_href ?>" method="post">
   <input type="hidden" name="action" value="delete" />
   <p><strong>Etes-vous sur de vouloir <?cs
    if:!?wiki.version ?>définitivement <?cs 
    /if ?>effacer <?cs var:version_range ?>cette page?</strong><br /><?cs
   if:wiki.only_version ?>
    Cette version est la seule de cette page, la page va donc être définitivement 
    supprimée!<?cs
   /if ?><?cs
   if:?wiki.version ?>
    <input type="hidden" name="version" value="<?cs var:wiki.version ?>" /><?cs
   /if ?><?cs
   if:wiki.old_version ?>
    <input type="hidden" name="old_version" value="<?cs var:wiki.old_version ?>" /><?cs
   /if ?>
   Cette opération est irréversible.</p>
   <div class="buttons">
    <input type="submit" name="cancel" value="Annuler" />
    <input type="submit" value="Supprimer <?cs var:delete_what ?>" />
   </div>
  </form>
 
 <?cs elif:wiki.action == "diff" ?>
  <h1>Modifications <?cs
    if:wiki.old_version ?>entre 
     <a href="<?cs var:wiki.current_href ?>?version=<?cs var:wiki.old_version?>">la version <?cs var:wiki.old_version?></a> et <?cs
    else ?>de <?cs
    /if ?>
    <a href="<?cs var:wiki.current_href ?>?version=<?cs var:wiki.version?>">la version <?cs var:wiki.version?></a> de 
    <a href="<?cs var:wiki.current_href ?>"><?cs var:wiki.page_name ?></a></h1>
  <form method="post" id="prefs" action="<?cs var:wiki.current_href ?>">
   <div>
    <input type="hidden" name="action" value="diff" />
    <input type="hidden" name="version" value="<?cs var:wiki.version ?>" />
    <input type="hidden" name="old_version" value="<?cs var:wiki.old_version ?>" />
    <label>Afficher les différences <select name="style">
     <option value="inline"<?cs
       if:diff.style == 'inline' ?> selected="selected"<?cs
       /if ?>>au fil</option>
     <option value="sidebyside"<?cs
       if:diff.style == 'sidebyside' ?> selected="selected"<?cs
       /if ?>>côte à côte</option>
    </select></label>
    <div class="field">
     Afficher <input type="text" name="contextlines" id="contextlines" size="2"
       maxlength="3" value="<?cs var:diff.options.contextlines ?>" />
     <label for="contextlines">lignes entourant chaque modification</label>
    </div>
    <fieldset id="ignore">
     <legend>Ignorer :</legend>
     <div class="field">
      <input type="checkbox" id="blanklines" name="ignoreblanklines"<?cs
        if:diff.options.ignoreblanklines ?> checked="checked"<?cs /if ?> />
      <label for="blanklines">Lignes vides</label>
     </div>
     <div class="field">
      <input type="checkbox" id="case" name="ignorecase"<?cs
        if:diff.options.ignorecase ?> checked="checked"<?cs /if ?> />
      <label for="case">Différences majuscule/minuscule</label>
     </div>
     <div class="field">
      <input type="checkbox" id="whitespace" name="ignorewhitespace"<?cs
        if:diff.options.ignorewhitespace ?> checked="checked"<?cs /if ?> />
      <label for="whitespace">Différences d'espacement</label>
     </div>
    </fieldset>
    <div class="buttons">
     <input type="submit" name="update" value="Actualiser" />
    </div>
   </div>
  </form>
  <dl id="overview">
   <dt class="property author">Auteur :</dt>
   <dd class="author"><?cs
    if:wiki.num_changes > 1 ?><em class="multi">(modifications multiples)</em><?cs
    else ?><?cs var:wiki.author ?> <span class="ipnr">(IP: <?cs
     var:wiki.ipnr ?>)</span><?cs
    /if ?></dd>
   <dt class="property time">Date :</dt>
   <dd class="time"><?cs
    if:wiki.num_changes > 1 ?><em class="multi">(modifications multiples)</em><?cs
    elif:wiki.time ?><?cs var:wiki.time ?> (<?cs var:wiki.time_delta ?> ago)<?cs
    else ?>--<?cs
    /if ?></dd>
   <dt class="property message">Commentaire :</dt>
   <dd class="message"><?cs
    if:wiki.num_changes > 1 ?><em class="multi">(modifications multiples)</em><?cs
    else ?><?cs var:wiki.comment ?><?cs /if ?></dd>
  </dl>
  <div class="diff">
   <div id="legend">
    <h3>Légende :</h3>
    <dl>
     <dt class="unmod"></dt><dd>Non modifié</dd>
     <dt class="add"></dt><dd>Ajouté</dd>
     <dt class="rem"></dt><dd>Supprimé</dd>
     <dt class="mod"></dt><dd>Modifié</dd>
    </dl>
   </div>
   <ul class="entries">
    <li class="entry">
     <h2><?cs var:wiki.page_name ?></h2><?cs
      if:diff.style == 'sidebyside' ?>
      <table class="sidebyside" summary="Différences">
       <colgroup class="l"><col class="lineno" /><col class="content" /></colgroup>
       <colgroup class="r"><col class="lineno" /><col class="content" /></colgroup>
       <thead><tr>
        <th colspan="2">Version <?cs var:wiki.old_version ?></th>
        <th colspan="2">Version <?cs var:wiki.version ?></th>
       </tr></thead><?cs
       each:change = wiki.diff ?><?cs
        call:diff_display(change, diff.style) ?><?cs
       /each ?>
      </table><?cs
     else ?>
      <table class="inline" summary="Différences">
       <colgroup><col class="lineno" /><col class="lineno" /><col class="content" /></colgroup>
       <thead><tr>
        <th title="Version <?cs var:wiki.old_version ?>">v<?cs
          alt:wiki.old_version ?>0<?cs /alt ?></th>
        <th title="Version <?cs var:wiki.version ?>">v<?cs
          var:wiki.version ?></th>
        <th>&nbsp;</th>
       </tr></thead><?cs
       each:change = wiki.diff ?><?cs
        call:diff_display(change, diff.style) ?><?cs
       /each ?>
      </table><?cs
     /if ?>
    </li>
   </ul><?cs
   if:trac.acl.WIKI_DELETE && 
    (len(wiki.diff) == 0 || wiki.version == wiki.latest_version) ?>
    <form method="get" action="<?cs var:wiki.current_href ?>">
     <input type="hidden" name="action" value="delete" />
     <input type="hidden" name="version" value="<?cs var:wiki.version ?>" />
     <input type="hidden" name="old_version" value="<?cs var:wiki.old_version ?>" />
     <input type="submit" name="delete_version" value="Supprimer <?cs
     if:wiki.version - wiki.old_version > 1 ?>les versions <?cs 
      var:wiki.old_version+1 ?> à <?cs else ?>la version <?cs
     /if ?><?cs var:wiki.version ?>" />
    </form><?cs
   /if ?>
  </div>

 <?cs elif wiki.action == "history" ?>
  <h1>Historique des modifications de <a href="<?cs var:wiki.current_href ?>"><?cs
    var:wiki.page_name ?></a></h1>
  <?cs if:len(wiki.history) ?><form class="printableform" method="get" action="">
   <input type="hidden" name="action" value="diff" />
   <div class="buttons">
    <input type="submit" value="Voir les modifications" />
   </div>
   <table id="wikihist" class="listing" summary="Historique des modifications">
    <thead><tr>
     <th class="diff"></th>
     <th class="version">Version</th>
     <th class="date">Date</th>
     <th class="author">Auteur</th>
     <th class="comment">Commentaire</th>
    </tr></thead>
    <tbody><?cs each:item = wiki.history ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="diff"><input type="radio" name="old_version" value="<?cs
        var:item.version ?>"<?cs
        if:name(item) == 1 ?> checked="checked"<?cs
        /if ?> /> <input type="radio" name="version" value="<?cs
        var:item.version ?>"<?cs
        if:name(item) == 0 ?> checked="checked"<?cs
        /if ?> /></td>
      <td class="version"><a href="<?cs
        var:item.url ?>" title="View this version"><?cs
        var:item.version ?></a></td>
      <td class="date"><?cs var:item.time ?></td>
      <td class="author" title="Adresse IP: <?cs var:item.ipaddr ?>"><?cs 
        var:item.author ?></td>
      <td class="comment"><?cs var:item.comment ?></td>
     </tr>
    <?cs /each ?></tbody>
   </table><?cs
   if:len(wiki.history) > #10 ?>
    <div class="buttons">
     <input type="submit" value="Voir les modifications" />
    </div><?cs
   /if ?>
  </form><?cs /if ?>
 
 <?cs else ?>
  <?cs if wiki.action == "edit" || wiki.action == "preview" || wiki.action == "collision" ?>
   <h1>Edition "<?cs var:wiki.page_name ?>"</h1><?cs
    if wiki.action == "preview" ?>
     <table id="info" summary="Revision info"><tbody><tr>
       <th scope="col">
        Aperçu de la nouvelle version <?cs var:$wiki.version+1 ?> (modifié par <?cs var:wiki.author ?>)
       </th></tr><tr>
       <td class="message"><?cs var:wiki.comment_html ?></td>
      </tr>
     </tbody></table>
     <fieldset id="preview">
      <legend>Aperçu (<a href="#edit">passer</a>)</legend>
        <div class="wikipage"><?cs var:wiki.page_html ?></div>
     </fieldset><?cs
     elif wiki.action =="collision"?>
     <div class="system-message">
       Désolé, cette page a été modifiée par quelqu'un d'autre depuis que vous
       avez débuté l'édition. Vos modifications ne peuvent être enregistrées.
     </div><?cs
    /if ?>
   <form id="edit" action="<?cs var:wiki.current_href ?>" method="post">
    <fieldset class="iefix">
     <input type="hidden" name="action" value="edit" />
     <input type="hidden" name="version" value="<?cs var:wiki.version ?>" />
     <input type="hidden" id="scroll_bar_pos" name="scroll_bar_pos" value="<?cs
       var:wiki.scroll_bar_pos ?>" />
     <div id="rows">
      <label for="editrows">Ajuster la hauteur de la fenêtre d'édition:</label>
      <select size="1" name="editrows" id="editrows" tabindex="43"
        onchange="resizeTextArea('text', this.options[selectedIndex].value)"><?cs
       loop:rows = 8, 42, 4 ?>
        <option value="<?cs var:rows ?>"<?cs
          if:rows == wiki.edit_rows ?> selected="selected"<?cs /if ?>><?cs
          var:rows ?></option><?cs
       /loop ?>
      </select>
     </div>
     <p><textarea id="text" class="wikitext" name="text" cols="80" rows="<?cs
       var:wiki.edit_rows ?>">
<?cs var:wiki.page_source ?></textarea></p>
     <script type="text/javascript">
       var scrollBarPos = document.getElementById("scroll_bar_pos");
       var text = document.getElementById("text");
       addEvent(window, "load", function() {
         if (scrollBarPos.value) text.scrollTop = scrollBarPos.value;
       });
       addEvent(text, "blur", function() { scrollBarPos.value = text.scrollTop });
     </script>
    </fieldset>
    <div id="help">
     <b>Note:</b> Voir <a href="<?cs var:$trac.href.wiki
?>/WikiFormatting">WikiFormatting</a> et <a href="<?cs var:$trac.href.wiki
?>/TracWiki">TracWiki</a> pour de l'aide sur l'édition de page Wiki.
    </div>
    <fieldset id="changeinfo">
     <legend>Informations sur les modifications</legend>
     <?cs if:trac.authname == "anonymous" ?>
      <div class="field">
       <label>Your email or username:<br />
       <input id="author" type="text" name="author" size="30" value="<?cs
         var:wiki.author ?>" /></label>
      </div>
     <?cs /if ?>
     <div class="field">
      <label>Description (optionnelle) des modifications apportées:<br />
      <input id="comment" type="text" name="comment" size="60" value="<?cs
        var:wiki.comment?>" /></label>
     </div><br />
     <?cs if trac.acl.WIKI_ADMIN ?>
      <div class="options">
       <label><input type="checkbox" name="readonly" id="readonly" <?cs
         if wiki.readonly == "1"?>checked="checked"<?cs /if ?> />
       Page non modifiable</label>
      </div>
     <?cs /if ?>
    </fieldset>
    <div class="buttons"><?cs
     if wiki.action == "collision" ?>
      <input type="submit" name="preview" value="Aperçu" disabled="disabled" />&nbsp;
      <input type="submit" name="save" value="Enregistrer les modifications" disabled="disabled" />&nbsp;
     <?cs else ?>
      <input type="submit" name="preview" value="Aperçu" accesskey="a" />&nbsp;
      <input type="submit" name="save" value="Enregistrer les modifications" />&nbsp;
     <?cs /if ?>
     <input type="submit" name="cancel" value="Annuler" />
    </div>
    <script type="text/javascript" src="<?cs
      var:htdocs_location ?>js/wikitoolbar.js"></script>
   </form>
  <?cs /if ?>
  <?cs if wiki.action == "view" ?>
   <?cs if:wiki.comment_html ?>
    <table id="info" summary="Revision info"><tbody><tr>
      <th scope="col">
       Version <?cs var:wiki.version ?> (modifié par <?cs var:wiki.author ?>, <?cs var:wiki.age ?> ago)
      </th></tr><tr>
      <td class="message"><?cs var:wiki.comment_html ?></td>
     </tr>
    </tbody></table>
   <?cs /if ?>
   <div class="wikipage">
    <div id="searchable"><?cs var:wiki.page_html ?></div>
   </div>
   <?cs if:len(wiki.attachments) ?>
    <h3 id="tkt-changes-hdr">Pièces jointes</h3>
    <ul class="tkt-chg-list"><?cs
     each:attachment = wiki.attachments ?><li class="tkt-chg-change"><a href="<?cs
      var:attachment.href ?>"><?cs
      var:attachment.filename ?></a> (<?cs var:attachment.size ?>) -<?cs
      if:attachment.description ?><q><?cs var:attachment.description ?></q>,<?cs
      /if ?> ajouté par <?cs var:attachment.author ?> le <?cs
      var:attachment.time ?>.</li><?cs
     /each ?>
    </ul>
  <?cs /if ?>
  <?cs if wiki.action == "view" && (trac.acl.WIKI_MODIFY || trac.acl.WIKI_DELETE)
      && (wiki.readonly == "0" || trac.acl.WIKI_ADMIN) ?>
   <div class="buttons"><?cs
    if:trac.acl.WIKI_MODIFY ?>
     <form method="get" action="<?cs var:wiki.current_href ?>"><div>
      <input type="hidden" name="action" value="edit" />
      <input type="submit" value="<?cs if:wiki.exists ?>Editer<?cs
        else ?>Créer<?cs /if ?> cette page" accesskey="e" />
     </div></form><?cs
     if:wiki.exists ?>
      <form method="get" action="<?cs var:wiki.attach_href ?>"><div>
       <input type="hidden" name="action" value="new" />
       <input type="submit" value="Joindre un fichier" />
      </div></form><?cs
     /if ?><?cs
    /if ?><?cs
    if:wiki.exists && trac.acl.WIKI_DELETE ?>
     <form method="get" action="<?cs var:wiki.current_href ?>"><div id="delete">
      <input type="hidden" name="action" value="delete" />
      <input type="hidden" name="version" value="<?cs var:wiki.version ?>" /><?cs
      if:wiki.version == wiki.latest_version ?>
       <input type="submit" name="delete_version" value="Supprimer cette version" /><?cs
      /if ?>
      <input type="submit" value="Supprimer cette page" />
     </div></form>
    <?cs /if ?>
   </div>
  <?cs /if ?>
  <script type="text/javascript">
   addHeadingLinks(document.getElementById("searchable"), "Link to this section");
  </script>
 <?cs /if ?>
 <?cs /if ?>
</div>

<?cs include "footer.cs" ?>

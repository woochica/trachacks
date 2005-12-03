<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <ul>
  <li class="last"><a href="<?cs var:browser.log_href ?>">Journal des révisions</a></li>
 </ul>
</div>

<div id="content" class="browser">
 <h1><?cs call:browser_path_links(browser.path, browser) ?></h1>

 <div id="jumprev">
  <form action="" method="get"><div>
   <label for="rev">Voir la révision:</label>
    <input type="text" id="rev" name="rev" value="<?cs
      var:browser.revision?>" size="4" />
  </div></form>
 </div>

 <?cs if:browser.is_dir ?>
  <table class="listing" id="dirlist">
   <thead>
    <tr><?cs 
     call:sortable_th(browser.order, browser.desc, 'name', 'Nom', browser.href) ?><?cs 
     call:sortable_th(browser.order, browser.desc, 'size', 'Taille', browser.href) ?>
     <th class="rev">Rév.</th><?cs 
     call:sortable_th(browser.order, browser.desc, 'date', 'Age', browser.href) ?>
     <th class="change">Dernière modification</th>
    </tr>
   </thead>
   <tbody>
    <?cs if:len(chrome.links.up) ?>
     <tr class="even">
      <td class="name" colspan="5">
       <a class="parent" title="Répertoire parent" href="<?cs
         var:chrome.links.up.0.href ?>">../</a>
      </td>
     </tr>
    <?cs /if ?>
    <?cs each:item = browser.items ?>
     <?cs set:change = browser.changes[item.rev] ?>
     <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
      <td class="name"><?cs
       if:item.is_dir ?><?cs
        if:item.permission ?>
         <a class="dir" title="Parcourir le répertoire" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="dir" title="Accès refusé" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       else ?><?cs
        if:item.permission != '' ?>
         <a class="file" title="Voir le fichier" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="file" title="Accès refusé" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       /if ?>
      </td>
      <td class="size"><?cs var:item.size ?></td>
      <td class="rev"><?cs if:item.permission != '' ?><a title="Voir le journal des révisions" href="<?cs
        var:item.log_href ?>"><?cs var:item.rev ?></a><?cs else ?><?cs var:item.rev ?><?cs /if ?></td>
      <td class="age"><span title="<?cs var:browser.changes[item.rev].date ?>"><?cs
        var:browser.changes[item.rev].age ?></span></td>
      <td class="change">
       <span class="author"><?cs var:browser.changes[item.rev].author ?>:</span>
       <span class="change"><?cs var:browser.changes[item.rev].message ?></span>
      </td>
     </tr>
    <?cs /each ?>
   </tbody>
  </table><?cs
 /if ?><?cs

 if:len(browser.props) || !browser.is_dir ?>
  <table id="info" summary="Info révisions"><?cs
   if:!browser.is_dir ?><tr>
    <th scope="row">
     Révision <a href="<?cs var:file.changeset_href ?>"><?cs var:file.rev ?></a>
     (déposée par <?cs var:file.author ?>, <?cs var:file.age ?> ago)
    </th>
    <td class="message"><?cs var:file.message ?></td>
   </tr><?cs /if ?><?cs
   if:len(browser.props) ?><tr>
    <td colspan="2"><ul class="props"><?cs
     each:prop = browser.props ?>
      <li>Propriété <strong><?cs var:name(prop) ?></strong> définie à <em><code><?cs
      var:prop ?></code></em></li><?cs
     /each ?>
    </ul></td><?cs
   /if ?></tr>
  </table><?cs
 /if ?><?cs
 
 if:!browser.is_dir ?>
  <div id="preview"><?cs
   if:file.preview ?><?cs
    var:file.preview ?><?cs
   elif:file.max_file_size_reached ?>
    <strong>Prévisualiation HTML non disponible</strong>, car la taille du 
    fichier excède <?cs var:file.max_file_size ?> octets. Essayez plutôt de 
    <a href="<?cs var:file.raw_href ?>">télécharger</a> le fichier.<?cs
   else ?><strong>Prévisualiation HTML non disponible</strong>. Pour voir le 
   contenu du fichier, <a href="<?cs var:file.raw_href ?>">téléchargez</a>-le.
   <?cs /if ?>
  </div><?cs
 /if ?>

 <div id="help">
  <strong>Note:</strong> Voir <a href="<?cs var:trac.href.wiki
  ?>/TracBrowser">TracBrowser</a> pour de l'aide sur l'utilisation du Navigateur.
 </div>

</div>
<?cs include:"footer.cs"?>

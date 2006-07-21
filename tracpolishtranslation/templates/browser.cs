<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <ul>
  <li class="last"><a href="<?cs var:browser.log_href ?>">Log rewizji</a></li>
 </ul>
</div>

<div id="content" class="browser">
 <h1><?cs call:browser_path_links(browser.path, browser) ?></h1>

 <div id="jumprev">
  <form action="" method="get"><div>
   <label for="rev">Podgl±d rewizji:</label>
   <input type="text" id="rev" name="rev" value="<?cs
     var:browser.revision ?>" size="4" />
  </div></form>
 </div>

 <?cs if:browser.is_dir ?>
  <table class="listing" id="dirlist">
   <thead>
    <tr><?cs 
     call:sortable_th(browser.order, browser.desc, 'name', 'Name', browser.href) ?><?cs 
     call:sortable_th(browser.order, browser.desc, 'size', 'Size', browser.href) ?>
     <th class="rev">Rew</th><?cs 
     call:sortable_th(browser.order, browser.desc, 'date', 'Age', browser.href) ?>
     <th class="change">Ostatania zmiana</th>
    </tr>
   </thead>
   <tbody>
    <?cs if:len(chrome.links.up) ?>
     <tr class="even">
      <td class="name" colspan="5">
       <a class="parent" title="Poziom wy¿ej" href="<?cs
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
         <a class="dir" title="Przegl±daj katalog" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="dir" title="Brak dostêpu" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       else ?><?cs
        if:item.permission != '' ?>
         <a class="file" title="Podgl±d pliku" href="<?cs
           var:item.browser_href ?>"><?cs var:item.name ?></a><?cs
        else ?>
         <span class="file" title="Brak dostêpu" href=""><?cs
           var:item.name ?></span><?cs
        /if ?><?cs
       /if ?>
      </td>
      <td class="size"><?cs var:item.size ?></td>
      <td class="rev"><?cs if:item.permission != '' ?><a title="Podgl±d rewizji" href="<?cs
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
  <table id="info" summary="Szczegó³y rewizji"><?cs
   if:!browser.is_dir ?><tr>
    <th scope="row">
     Rewizja <a href="<?cs var:file.changeset_href ?>"><?cs var:file.rev ?></a>
     (checked in by <?cs var:file.author ?>, <?cs var:file.age ?> ago)
    </th>
    <td class="message"><?cs var:file.message ?></td>
   </tr><?cs /if ?><?cs
   if:len(browser.props) ?><tr>
    <td colspan="2"><ul class="props"><?cs
     each:prop = browser.props ?>
      <li>W³a¶ciwo¶æ <strong><?cs var:name(prop) ?></strong> ustawiona na <em><code><?cs
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
    <strong>Podgl±d HTML nie jest mo¿liwy</strong>, poniewa¿ plik jest zbyt du¿y
    <?cs var:file.max_file_size ?>. Spróbuj <a href="<?cs
    var:file.raw_href ?>">pobraæ</a> plik.<?cs
   else ?><strong>Podgl±d HTML nie jest mo¿liwy</strong>. Aby obejrzeæ plik, <a href="<?cs
    var:file.raw_href ?>">pobierz</a> go.<?cs
   /if ?>
  </div><?cs
 /if ?>

 <div id="help">
  <strong>Pomoc:</strong> Zobacz <a href="<?cs var:trac.href.wiki
  ?>/TracBrowser">TracBrowser</a> aby uzyskaæ informacje.
 </div>

</div>
<?cs include:"footer.cs"?>

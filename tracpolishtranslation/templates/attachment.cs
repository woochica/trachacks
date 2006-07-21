<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="attachment">

<?cs if:attachment.mode == 'new' ?>
 <h1>Dodaj za³±cznik do <a href="<?cs var:attachment.parent.href?>"><?cs
   var:attachment.parent.name ?></a></h1>
 <form id="attachment" method="post" enctype="multipart/form-data" action="">
  <div class="field">
   <label>Plik:<br /><input type="file" name="attachment" /></label>
  </div>
  <fieldset>
   <legend>Info</legend>
   <div class="field">
    <label>Twój adres email lub nazwa u¿ytkownika:<br />
    <input type="text" name="author" size="30" value="<?cs
      var:attachment.author?>" /></label>
   </div>
   <div class="field">
    <label>Opis pliku (opcja):<br />
    <input type="text" name="description" size="60" /></label>
   </div>
   <br />
   <div class="options">
    <label><input type="checkbox" name="replace" />
    Zast±p istniej±cy za³±cznik o tej samej nazwie</label>
   </div>
   <br />
  </fieldset>
  <div class="buttons">
   <input type="hidden" name="action" value="new" />
   <input type="hidden" name="type" value="<?cs var:attachment.parent.type ?>" />
   <input type="hidden" name="id" value="<?cs var:attachment.parent.id ?>" />
   <input type="submit" value="Za³±cz" />
   <input type="submit" name="cancel" value="Anuluj" />
  </div>
 </form>
<?cs elif:attachment.mode == 'delete' ?>
 <h1><a href="<?cs var:attachment.parent.href ?>"><?cs
   var:attachment.parent.name ?></a>: <?cs var:attachment.filename ?></h1>
 <p><strong>Czy jeste¶ pewny, ¿e chcesz usun±æ ten za³±cznik?</strong><br />
 Ta operacja jest nieodwracalna.</p>
 <div class="buttons">
  <form method="post" action=""><div id="delete">
   <input type="hidden" name="action" value="delete" />
   <input type="submit" name="cancel" value="Cancel" />
   <input type="submit" value="Usuñ" />
  </div></form>
 </div><?cs else ?>
 <h1><a href="<?cs var:attachment.parent.href ?>"><?cs
   var:attachment.parent.name ?></a>: <?cs var:attachment.filename ?></h1>
 <div id="preview"><?cs
  if:attachment.preview ?>
   <?cs var:attachment.preview ?><?cs
  elif:attachment.max_file_size_reached ?>
   <strong>Podgl±d HTML nie jest dostêpny</strong>, poniewa¿ plik jest zbyt du¿y
   <?cs var:attachment.max_file_size  ?>. Mo¿esz <a href="<?cs
     var:attachment.raw_href ?>">pobraæ</a> ten plik.<?cs
  else ?>
   <strong>Podgl±d HTML nie jest dostêpny</strong>. Aby obejrzeæ ten plik, musisz go
   <a href="<?cs var:attachment.raw_href ?>">pobraæ</a>.<?cs
  /if ?>
 </div>
 <?cs if:attachment.can_delete ?><div class="buttons">
  <form method="get" action=""><div id="delete">
   <input type="hidden" name="action" value="delete" />
   <input type="submit" value="Usuñ" />
  </div></form>
 </div><?cs /if ?>
<?cs /if ?>

</div>
<?cs include "footer.cs"?>

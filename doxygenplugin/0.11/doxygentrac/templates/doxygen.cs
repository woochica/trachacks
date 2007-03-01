<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs if:doxygen.text ?>
  <?cs if:doxygen.wiki_page ?>
   <div id="ctxtnav" class="nav">
    <h2>Doxygen Navigation</h2>
    <ul><li class="first last"><a href="<?cs var:doxygen.wiki_href ?>">
       View <?cs var:doxygen.wiki_page ?></a></li>
    </ul>
   </div>
  <?cs /if ?>
  <div id="content" class="wiki">
    <div class="wikipage">
      <div id="searchable">
        <?cs var:doxygen.text ?>
      </div>
   </div>
<?cs else ?>
  <?cs include doxygen.path ?>
<?cs /if ?>

<?cs include "footer.cs"?>

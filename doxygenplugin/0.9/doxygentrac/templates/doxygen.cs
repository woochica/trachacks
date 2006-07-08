<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs if:doxygen.text ?>
  <div id="content" class="wiki">
    <div class="wikipage">
      <div id="searchable">
        <?cs var:doxygen.text ?>
      </div>
   </div>
<?cs else ?>
  <?cs include: doxygen.path ?>
<?cs /if ?>

<?cs include "footer.cs"?>

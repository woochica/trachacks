<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<form method="post" action="<?cs var:estimate.href ?>" >

<div id="content" class="estimate">
  <div id="messages" >
    <?cs each:item = estimate.messages ?>
      <div class="message" ><?cs var:item ?></div>
    <?cs /each ?>
  </div>
</div>

</form>
<?cs include "footer.cs"?>

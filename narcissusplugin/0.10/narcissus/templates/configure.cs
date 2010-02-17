<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
<?cs include "navigation.cs" ?>

<h1>Configure</h1>

<?cs if:subcount(user) > 0 ?>
  <form id="config" action="<?cs var:trac.href.configure ?>" method="post">
    <h2>Add group member:</h2>
    <select name="add" width="150" style="width: 150px">
      <?cs each:item = user ?>
        <option value="<?cs var:item ?>"><?cs var:item ?></option>
      <?cs /each ?>
    </select>
    <input type="submit" value="Add" />
  </form>
<?cs /if ?>

<?cs if:subcount(member) > 0 ?>
  <form id="config" action="<?cs var:trac.href.configure ?>" method="post">
    <h2>Remove group member:</h2>
    <select name="remove" width="150" style="width: 150px">
      <?cs each:item = member ?>
        <option value="<?cs var:item ?>"><?cs var:item ?></option>
      <?cs /each ?>
    </select>
    <input type="submit" value="Remove" />
  </form>
<?cs /if ?>

<form id="config" action="<?cs var:trac.href.configure ?>" method="post">
  <h2>Change score thresholds:</h2>
  <input type="hidden" name="bounds" />
  <?cs each:resource = bound ?>
    <p><label><?cs name:resource ?>:&nbsp;
    <?cs each:threshold = resource ?>
      <input type="text" size="3" name="<?cs name:resource ?>.<?cs name:threshold ?>" value="<?cs var:threshold ?>" />&nbsp;
    <?cs /each ?>
    </label></p>
  <?cs /each ?>
  <p><input type="submit" value="Submit" /></p>
</form>

<form id="config" action="<?cs var:trac.href.configure ?>" method="post">
  <h2>Change ticket credits:</h2>
  <input type="hidden" name="credits" />
  <?cs each:item = credit ?>
    <p><label><?cs name:item ?>:&nbsp;<input type="text" size="3" name="<?cs name:item ?>" value="<?cs var:item ?>" /></label></p>
  <?cs /each ?>
  <p><input type="submit" value="Submit" /></p>
</form>

<?cs include "footer.cs" ?>


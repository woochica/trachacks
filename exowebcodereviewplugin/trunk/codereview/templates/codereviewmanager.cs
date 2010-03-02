<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs include "nav.cs" ?>
<?cs if:action=='main' ?>
<fieldset>
<legend>Code Review Configure</legend>
<div class="wiki">
<form method="post" action="<?cs var:config.href ?>">
<table>
<tr>
  <td>notify_enabled : </td>
  <td>&nbsp;&nbsp;&nbsp;&nbsp; On <input type="radio" name="notify_enabled" value="true" <?cs if:notify_enabled == "true" ?>checked="true" <?cs /if ?>/>&nbsp;&nbsp;&nbsp;&nbsp; Off <input type="radio" name="notify_enabled" value="false" <?cs if:notify_enabled == "false" ?>checked="true" <?cs /if ?>/></td>
</tr>
<tr>
  <td>start_rev : </td>
  <td><input type="text" name="start_rev" value="<?cs var:start_rev ?>"></td>
</tr>
<tr>
  <td>absurl : </td>
  <td><input type="text" name="absurl" value="<?cs var:absurl ?>"></td>
</tr>
<tr>
  <td>teamlist : </td>
  <td><input type="text" name="team_list" value="<?cs var:team_list ?>"></td>
</tr>
</table>

<input type="hidden" name="action" value="config">
<div class="buttons">
<input type="submit" name="submit" value="Save">
</div>
</form>
</div>
</fieldset>

<?cs elif:action=='configok' ?>
<div id="content" class="wiki">
<h1><?cs var:description ?></h1>
<br />
[ <a href="<?cs var:manager_href ?>">Return CodeReviewManager</a> ]
</div>

<?cs /if ?>
<?cs include "footer.cs" ?>

<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<h2>Edit Gringlet</h2>

<?cs if:len(messages) ?>
<?cs   each:message = messages ?>
  <p style="color:red"><?cs var:message ?></p>
<?cs   /each ?>
<?cs /if ?>

   <form id="edit" method="post">
    <fieldset class="iefix">
     <input type="hidden" name="action" value="edit" />
     <input type="hidden" name="version" value="<?cs var:gringlet.version ?>" />
     <input type="hidden" id="scroll_bar_pos" name="scroll_bar_pos" value="<?cs
       var:wiki.scroll_bar_pos ?>" />
     <div id="rows">
      <label for="editrows">Adjust edit area height:</label>
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
<?cs var:gringlet.source ?></textarea></p>
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
     <b>Note:</b> See <a href="<?cs var:$trac.href.wiki
?>/WikiFormatting">WikiFormatting</a> and <a href="<?cs var:$trac.href.wiki
?>/TracWiki">TracWiki</a> for help on editing wiki content.
    </div>
    <fieldset>
      <legend>Access Control List</legend>
      <input type="text" id="acl" name="acl" size="80" value="<?cs
       var:gringlet.acl ?>"/>
    </fieldset>
    <div class="buttons">
     <input type="submit" name="save" value="Save Gringlet" />&nbsp;
     <!-- <input type="submit" name="cancel" value="Cancel" /> -->
    </div>
    <script type="text/javascript" src="<?cs
      var:htdocs_location ?>js/wikitoolbar.js"></script>
   </form>

<?cs include "footer.cs"?>

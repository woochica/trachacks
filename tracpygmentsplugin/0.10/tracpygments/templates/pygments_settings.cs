<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs each:s = styles ?>
 <link rel="stylesheet" href="<?cs var:pygments_path ?>/<?cs var:s ?>.css"
       type="text/css" title="<?cs var:s ?>" />
<?cs /each ?>

<div id="content">
 <div class="wrapper">
  <h1>Pygments Settings</h1>
  <p>
   The Pygments syntax highlighter can be used with
   different coloring themes.
  </p>
  <form action="<?cs var:pygments_path ?>" method="post">
   <select name="new_style" onchange="switchStylesheet(this.options[this.selectedIndex].text)">
    <?cs each:s = styles ?>
     <option<?cs if:s==current ?> selected="selected"<?cs /if ?>><?cs var:s ?></option>
    <?cs /each ?>
   </select>
   <input type="submit" value="Apply" />
  </form>
  <h2>Preview</h2>
  <?cs var:output ?>
 </div>
</div>

<script type="text/javascript">
  function switchStylesheet(title) {
    var stylesheets = document.getElementsByTagName("LINK");
    for (var i = 0; i < stylesheets.length; i++) {
      stylesheet = stylesheets[i];
      var t = stylesheet.getAttribute('title');
      if (t) {
        stylesheet.disabled = (t != title);
      }
    }
  }

  switchStylesheet("<?cs var:current ?>");
</script>

<?cs include "footer.cs" ?>

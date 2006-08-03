<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav"></div>

<div id="content" class="revtree">

<h1>Revision Tree</h1>

<form id="prefs" method="get" action="">
 <div>
  <fieldset id="properties">
   <legend>Filters</legend>
   <div class="field">
    <label for="branch">Branch</label>
    <select id="branch" name="branch"><?cs each:br = revtree.branches ?>
     <option value="<?cs var:br ?>" <?cs if:revtree.branch == br 
     ?>selected="selected"<?cs /if ?>><?cs var:br ?></option><?cs
    /each ?></select>
   </div>
   <div class="field">
    <label for="author">Author</label>
    <select id="author" name="author"><?cs each:auth = revtree.authors ?>
     <option value="<?cs var:auth ?>" <?cs if:revtree.author == auth 
     ?>selected="selected"<?cs /if ?>><?cs var:auth ?></option><?cs
    /each ?></select>
   </div>
  </fieldset>
  <fieldset id="limits">
   <legend>Revisions</legend>
   <div class="field">
    <input type="radio" id="limperiod" name="limits" value="limperiod" <?cs 
     if:revtree.limits == "limperiod" ?> checked="checked"<?cs /if ?>/>
    <label for="period">Show last </label>
    <select id="period" name="period">
     <?cs each:per = revtree.periods ?><option value="<?cs 
      var:per.value ?>" <?cs if:revtree.period == per.value 
      ?>selected="selected"<?cs /if ?>><?cs var:per.label ?></option>
      <?cs /each ?></select>
   </div>
   <div class="field">
    <input type="radio" id="limrev" name="limits" value="limrev" <?cs 
     if:revtree.limits == "limrev" ?> checked="checked"<?cs /if ?>/>
    <label for="revmin">From </label>
     <select id="revmin" name="revmin">
      <?cs each:rev = revtree.revisions ?><option value="<?cs 
      var:rev ?>" <?cs if:revtree.revmin == rev ?>selected="selected"<?cs 
      /if ?>><?cs var:rev?></option>
      <?cs /each ?></select>
    <label for="revmax">up to </label>
     <select id="revmax" name="revmax">
      <?cs each:rev = revtree.revisions ?><option value="<?cs 
      var:rev ?>" <?cs if:revtree.revmax == rev ?>selected="selected"<?cs 
      /if ?>><?cs var:rev ?></option>
      <?cs /each ?></select>
   </div>
  </fieldset>

  <script type="text/javascript">
    var limrev = document.getElementById("limrev");
    var limperiod = document.getElementById("limperiod");
    var updateActionFields = function() {
      enableControl('period', limperiod.checked);
      enableControl('revmin', limrev.checked);
      enableControl('revmax', limrev.checked);
    };
    addEvent(window, 'load', updateActionFields);
    addEvent(limperiod, 'click', updateActionFields);
    addEvent(limrev, 'click', updateActionFields);
  </script>

  <fieldset id="options">
   <legend>Options</legend>
   <div class="field">
    <input type="hidden" name="checkbox_btup">
    <input type="checkbox" id="btup" 
      name="btup" <?cs if:revtree.btup 
      ?>checked="checked"<?cs /if ?> value="1"/><label for="btup">Younger
      revisions on top</label>
   </div>
   <div class="field">
    <input type="hidden" name="checkbox_hideterm">
    <input type="checkbox" id="hideterm"
      name="hideterm" <?cs if:revtree.hideterm
      ?>checked="checked"<?cs /if ?> value="1"/><label for="hideterm">Hide 
      terminated branches</label>
   </div>
  </fieldset>
  <div class="buttons">
   <input type="submit" value="Update"/>
   <input type="submit" name="nocache" value="Rebuild"/>
  </div>
 </div>
</form>

<?cs if revtree.legend ?>
<div id="legend">
 <?cs var:revtree.legend ?>
</div>
<?cs /if ?>

<?cs if revtree.errormsg ?>
<div id="errormsg" class="error">
  <p class="message"><?cs var:revtree.errormsg ?></p>
</div>
<?cs else ?>
<p>
<?cs var:revtree.img ?>
</p>
<?cs /if ?>
</div>

<?cs include "footer.cs"?>

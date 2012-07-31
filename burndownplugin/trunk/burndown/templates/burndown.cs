<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="burndown">
 <h1>Burndown Chart</h1>
</div>

<form action="<?cs var:burndown.href ?>" method="get">
    <label for="selected_milestone">Select milestone:</label>
    <select id="selected_milestone" name="selected_milestone">
        <?cs each:mile = milestones ?>
            <option value="<?cs var:mile ?>" <?cs if:selected_milestone == mile ?> selected="selected"<?cs /if ?> >
                <?cs var:mile ?>
            </option>
        <?cs /each ?>
    </select>
    <div class="buttons">
        <input type="submit" value="Show Burndown Chart" />
    </div>
</form>

<br />

<!-- 3D barchart added: here -->
<!-- NOTE: Copy SWF file to C:\Python24\share\trac\htdocs and prefix filename with "<?cs var:chrome.href ?>/common/" -->
<!-- 3D barchart added: here -->
<OBJECT classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,0,0" width="620" height="500" id="MSColumn3D" >
  <param name="movie" value="<?cs var:chrome.href ?>/hw/swf/FCF_MSColumn3D.swf" />
  <param name="FlashVars" value="&dataXML=<?cs var:dataXML ?>" />
  <param name="quality" value="high" />
  <embed src="<?cs var:chrome.href ?>/hw/swf/FCF_MSColumn3D.swf" flashVars="&dataXML=<?cs var:dataXML ?>" quality="high" width="620" height="500" name="Column2D" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" />
</OBJECT>

<?cs include "footer.cs" ?>


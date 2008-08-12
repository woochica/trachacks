<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="content" class="tractab">
height:
<select onchange="document.getElementById('thisIframe').style.height = this.options[this.selectedIndex].value;">
    <option value="100px">100</option>
    <option value="200px">200</option>
    <option value="300px">300</option>
    <option value="400px">400</option>
    <option value="500px" selected="true">500</option>
    <option value="600px">600</option>
    <option value="700px">700</option>
    <option value="800px">800</option>
    <option></option>
</select>
<iframe id="thisIframe"  style="width:100%;height:500px;overflow:auto;" 
    src="<?cs var:tractab.url ?>" ></iframe>
</div>

<?cs include "footer.cs"?>

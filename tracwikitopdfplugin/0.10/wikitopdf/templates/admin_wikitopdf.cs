<h2>Generate Wiki to PDF</h2>

<script class="mod" type="text/javascript">
    function move_item(from, to) {
        var from_box = document.getElementById(from+'pages_select');
        var to_box = document.getElementById(to+'pages_select');
        for (var i = 0; i < from_box.options.length; i++) {
           var opt = from_box.options[i];
           if (opt.selected) {
               var newOpt = new Option( opt.text, opt.value );
               try {
                   to_box.add(newOpt, null); // standards compliant
               }
               catch (ex) {
                   to_box.add(newOpt);       // MSIE
               }
               from_box.remove(i);
               i--;
           }
        }
    }

    function reorder_item(from, dir) {
        var box = document.getElementById(from+'pages_select');
        var i = box.selectedIndex;
        var j = i + dir;
        if(j<0 || j>=box.options.length) { return }
        var temp = box.options[i];
        var temp2 = box.options[j];
        box.options[i] = new Option(temp2.value, temp2.value);
        box.options[j] = new Option(temp.value, temp.value);
        box.selectedIndex = j;
    }
    
    function compile_pages(form) {
        var arr = new Array();
        for(i=0;i<form.rightpages.options.length;i++) {
            arr.push(form.rightpages.options[i].value);
        }
        form.rightpages_all.value = arr.join(',');
        return 1;
    }
</script>

<form method="post" onsubmit="compile_pages(this);">

<fieldset>
	<legend>Book Properties</legend>
	<table>
	<tbody>
		<tr>
			<td>Title:</td>
			<td><input type="text" name="title" size="80"/></td>
		</tr>
		<tr>
			<td>Sub-title:</td>
			<td><input type="text" name="subject" size="80"/></td>
		</tr>
		<tr>
			<td>Version:</td>
			<td><input type="text" name="version" size="20" /></td>
		</tr>
		<tr>
			<td>Date:</td>
			<td><input type="text" name="date" size="20"/></td>
		</tr>
	</tbody>
	</table>
</fieldset>

<fieldset>
    <legend>Select pages</legend>
	    <table border="0" width="100%">
        <tr>
            <td align="left" colspan="2">All Pages</td>
        </tr>
        <tr>
            <td colspan="2">
                <select id="leftpages_select" name="leftpages" size="10" style="width: 100%;">
                    <?cs each:page = wikitopdf.leftpages ?>
                    <option value="<?cs var:page ?>"><?cs var:page ?></option>
                    <?cs /each ?>
                </select>
            </td>
	</tr>
	<tr>
            <td align="center" colspan="2">
                <input type="button" onclick="move_item('right', 'left')" value="/\" />
					 &nbsp;&nbsp; 
                <input type="button" onclick="move_item('left', 'right')" value="\/" />
            </td>
	</tr>	
	<tr>
            <td align="left" colspan="2">Selected Pages</td>
         </tr>
	 <tr>
	 	<td width="95%">
	                <select id="rightpages_select" name="rightpages" size="10" style="width: 100%;">
                    		<?cs each:page = wikitopdf.rightpages ?>
                    		<option value="<?cs var:page ?>"><?cs var:page ?></option>
                    		<?cs /each ?>
                	</select>
		</td>
		<td width="5%" align="center">
			<input type="button" onclick="reorder_item('right', -1)" value="/\" />
			<br><br>
			<input type="button" onclick="reorder_item('right', 1)" value="\/" />
		</td>
        </tr>
  </table>    
</fieldset>

<fieldset>
    <legend>Output Format</legend>
    <?cs each:format = wikitopdf.formats ?>
    <label><input type="radio" name="format" value="<?cs name:format ?>" <?cs if:name(format)==wikitopdf.default_format ?>checked="checked"<?cs /if ?> /><?cs var:format.name ?></label>
    <?cs /each ?>
</fieldset>

<input type="hidden" name="rightpages_all" value="" />
<div class="buttons">
    <input type="submit" name="create" value="Create" />
</div>
</form>

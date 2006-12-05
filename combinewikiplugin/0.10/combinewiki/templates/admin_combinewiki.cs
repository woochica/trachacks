<h2>Combine Wiki</h2>

<script class="mod" type="text/javascript">
    function move_item(from, to) {
        var from_box = document.getElementById(from+'pages_select');
        var to_box = document.getElementById(to+'pages_select');
        to_box.options[to_box.length] = from_box.options[from_box.selectedIndex];
        from_box.options[from_box.selectedIndex] = null;
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
    <legend>Title</legend>
    <input type="text" name="title" size="40"/>
</fieldset>
<fieldset>
    <legend>Select pages</legend>
    <table border="0">
        <tr>
            <td colspan="2" align="left">All Pages</td>
            <td colspan="2" align="right">Exported Pages</td>
        </tr>
        <tr>
            <td rowspan="4">
                <select id="leftpages_select" name="leftpages" size="10">
                    <?cs each:page = combinewiki.leftpages ?>
                    <option value="<?cs var:page ?>"><?cs var:page ?></option>
                    <?cs /each ?>
                </select>
            </td>
            <td align="left" valign="top">
                <input type="button" onclick="reorder_item('left', -1)" value="/\" />
            </td>
            <td align="right" valign="top">
                <input type="button" onclick="reorder_item('right', -1)" value="/\" />
            </td>
            <td rowspan="4">
                <select id="rightpages_select" name="rightpages" size="10">
                    <?cs each:page = combinewiki.rightpages ?>
                    <option value="<?cs var:page ?>"><?cs var:page ?></option>
                    <?cs /each ?>
                </select>
            </td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <input type="button" onclick="move_item('left', 'right')" value="->" />
            </td>
        </tr>
        <tr>
            <td colspan="2" align="center">            
                <input type="button" onclick="move_item('right', 'left')" value="<-" />
            </td>
        </tr>
        <tr>
            <td align="left" valign="bottom">
                <input type="button" onclick="reorder_item('left', 1)" value="\/" />
            </td>
            <td align="right" valign="bottom">
                <input type="button" onclick="reorder_item('right', 1)" value="\/" />
            </td>
        </tr>
    </table>    
</fieldset>
<fieldset>
    <legend>Output Format</legend>
    <?cs each:format = combinewiki.formats ?>
    <label><input type="radio" name="format" value="<?cs name:format ?>" <?cs if:name(format)==combinewiki.default_format ?>checked="checked"<?cs /if ?> /><?cs var:format.name ?></label>
    <?cs /each ?>
</fieldset>
<input type="hidden" name="rightpages_all" value="" />
<div class="buttons">
    <input type="submit" name="create" value="Create" />
</div>
</form>

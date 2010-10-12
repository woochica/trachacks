<style type="text/css">
.sel {
  text-decoration: underline;
}
</style>

<script type="text/javascript">
function initTags() {
    var el = document.getElementById('keywords');
    var currentTags = el.value.split(/\s+/);
    for(i in currentTags) {
        var link = document.getElementById('add_' + currentTags[i]);
        if(link)
            link.className = "sel";
    }
}

window.onload = initTags;

function addTag(w) {
    var el = document.getElementById('keywords');
    var orig = el.value;
    var newval = orig.replace(new RegExp('\\b' + w + '\\b'), '');
    var link = document.getElementById('add_' + w);
    if (orig != newval) {
        // remove tag.
        if(link) link.className = '';
    } else {
        newval = orig + (orig ? ' ' : '') + w;
        if(link) link.className = 'sel';
    }
    el.value = newval.replace(/^\s+/, '');
}
</script>

<fieldset id="keywords">
 <legend>Add Keywords</legend>
 <?cs
      each:keyword = keywords ?><a href="#" onclick="javascript:addTag('<?cs
        var:keyword.0 ?>'); return false;" id="add_<?cs 
        var:keyword.0 ?>" title="<?cs var:keyword.1 ?>"><?cs
        var:keyword.0 ?></a> <?cs /each ?>
</fieldset>

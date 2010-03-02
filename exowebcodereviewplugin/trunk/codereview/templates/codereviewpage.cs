<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<?cs include "nav.cs" ?>

<?cs if:page_class=="None" ?>

<?cs if:delete_info ?>
<div class="system-message">
     <?cs var:delete_info ?>
</div>
<br />
<?cs /if ?>

<div id="content" class="wiki">
<h2><?cs var:message ?></h2>
</div>
<div class="buttons">
<form method="post" action="<?cs var:create_href ?>">
<input type="submit" value="Create This CodeReview" name="submit" />
<input type="hidden" name="action" value="edit" />
</form>
</div>

<?cs elif:page_class=='View' ?>
<div class="wiki">
<h1>Code Review : <?cs var:cr_id ?></h1>
<a href="<?cs var:cs_href ?>" style="color:red">Change Set : <?cs var:cr_id ?></a>

<br />

<?cs if:delete_info ?>
<div class="system-message">
     <?cs var:delete_info ?>
</div>
<br />
<?cs /if ?>


<table>
  <tr>
    <td> Version : </td>
    <td><?cs var:version ?></td>
  </tr>
  <tr>
    <td> Reviewers : </td>
    <td><?cs var:authors ?></td>
  </tr>
  <tr>
    <td> Last Changed : </td>
    <td><?cs var:time ?></td>
  </tr>
  <tr>
    <td> Status : </td>
    <td><?cs var:status ?></td>
  </tr>
  <tr>
    <td> Priority : </td>
    <td><?cs var:priority ?></td>
  </tr>
</table>

<br />

<fieldset>
<legend>Description</legend>
<div>
<?cs var:text ?>
</div>
</fieldset>
<br />
<?cs if:source_text ?>
<fieldset>
<legend>Source</legend>
<textarea class="wikitext" rows="20" cols="90" >
<?cs var:source_text ?>
</textarea>
</fieldset>

<br />
<?cs /if ?>
<?cs include "attachments.cs" ?>
<br />

<div class="buttons">
<form method="post" action="<?cs var:edit_href ?>" >
<input type="submit" name="submit" value="Edit this CodeReview" />
<input type="hidden" name="action" value="edit" />
</form>

<?cs if:delete_href ?>
<!--
<form method="post" action="<?cs var:delete_href ?>" >

<input type="submit" name="submit" value="Delete current version of this CodeReview" />

<input type="hidden" name="action" value="delete" />
</form>
-->

<?cs /if ?>
<input type="button" name="history" value="history" onclick="window.location='<?cs var:edit_href ?>?action=history'" />


</div>
</div>

<?cs elif:page_class=='edit' ?>

<script type="text/javascript" language="javascript">
  function review_submit(action)
  {
    document.getElementById('submit_action').value = action;
    document.getElementById('edit_form').submit();
    return true;
  }
  function autoresize()
  {
    t = document.getElementById("text");
    if(t.value.split('\n').length>t.rows)
    {
      t.rows = t.value.split('\n').length + 4;
    }
  }
</script>

<div class="wiki">
<h1>Code Review : <?cs var:id ?></h1>
<a style="color=red" href="<?cs var:cs_href ?>">Change Set : <?cs var:id ?></a>
<br />
<table>
  <tr>
    <td> Version : </td>
    <td><?cs var:version ?></td>
  </tr>
  <tr>
    <td> Reviewers : </td>
    <td><?cs if:reviewers=='' ?>None<?cs else ?><?cs var:reviewers ?><?cs /if ?></td>
  </tr>
  <tr>
    <td> Status : </td>
    <td><?cs if:status=="1" ?>Incomplete<?cs elif:status=="0" ?>Completed<?cs elif:status=="-1" ?>No need to review<?cs /if ?></td>
  </tr>
  <tr>
    <td> Priority : </td>
    <td><?cs var:priority ?></td>
  </tr>
  <?cs if:time!='' ?>
    <tr>
      <td> Last Changed : </td>
      <td><?cs var:time ?></td>
    </tr>
  <?cs /if ?>
</table>
<br />

<?cs if:oldtext ?>
<div class="system-message">

       Sorry, this page has been modified by somebody else since you started 
       editing. Your changes cannot be saved.
</div>
<?cs /if ?>


<?cs include "attachments.cs" ?>
<br />

<?cs if:preview ?>
<fieldset id="preview">
  <legend>Preview</legend>
  <div class="wikipage">
  <?cs var:preview ?>
  </div>
</fieldset>

<br />
<?cs /if ?>

<form method="post" action="<?cs var:save_href ?>" id="edit_form">
<div class="field">
  <label for="author">Your email or username:</label><br>
  <input type="text" id="author" name="author" size="40" value="<?cs var:author ?>" />
  <input type="hidden" id="text_width" name="text_width" value="90" />
</div>
<fieldset>
  <legend>CodeReview content</legend>
  <div class="field">
    <h1>Full description (You may use WikiFormatting here)</h1>
    <p>
    <textarea id="text" name="text" class="wikitext" rows="30" cols="90" style="width:100%" onkeyup="autoresize()"><?cs if:oldtext ?><?cs var:oldtext ?><?cs else ?><?cs var:text ?><?cs /if ?></textarea></p>
   </div>
  <input type="button" id="preview" value="Preview" onclick="review_submit('preview')" <?cs if:oldtext ?>disabled="disabled"<?cs /if ?> />
</fieldset>
<br />
<fieldset>
  <legend>Status</legend>
  
  <input type="radio" id="Uncompleted" name="status" value="1" <?cs if:status=="1" ?>checked="checked"<?cs /if ?> />
  <label for="Uncompleted">Undergoing review</label><br />
  <input type="radio" id="Completed" name="status" value="0" <?cs if:status=="0" ?>checked="checked"<?cs /if ?> />
  <label for="Completed">Completely reviewed</label><br />
  <input type="radio" id="Nntr" name="status" value="-1" <?cs if:status=="-1" ?>checked="checked"<?cs /if ?> />
  <label for="Nntr">No need to review</label><br />
</fieldset>
<br />

<fieldset>
  <legend>Priority</legend>
  
  <input type="radio" id="Normal" name="priority" value="normal" <?cs if:priority=="normal" ?>checked="checked"<?cs /if ?> />
  <label for="Normal">Normal</label><br />
  <input type="radio" id="Critical" name="priority" value="critical" <?cs if:priority=="critical" ?>checked="checked"<?cs /if ?> />
  <label for="Critical">Critical</label><br />
</fieldset>
<br />


<div class="buttons">
  <input type="button" value="Submit changes" onclick="review_submit('save')" <?cs if:oldtext ?>disabled="disabled"<?cs /if ?> />
  <input type="hidden" name="action" id="submit_action" />
  <input type="hidden" name="req_version" id="version" value="<?cs var:version ?>" />
</div>

<script type="text/javascript" language="javascript">
     <?cs if:source_count ?>
     var sourcelists = new Array(<?cs each:item=sourcelists ?>"<?cs var:item.v ?>"<?cs if:item.i+1<source_count ?>, <?cs /if ?><?cs /each ?>);
     <?cs else ?>
     var sourcelists = new Array("")
     <?cs /if ?>

(function($){
  window.addCodeReviewToolbar = function(textarea) {
    if ((document.selection == undefined)
     && (textarea.setSelectionRange == undefined)) {
      return;
    }
  
    var toolbar = document.createElement("div");
    toolbar.className = "codereviewtoolbar";
  
    function addInsertButton(id, title, fn) {
    var button = document.createElement("input");
    button.value = "Source";
    button.id = id;
    button.type = "button";
    button.title = title;
    button.onclick = function(){
                                 list = document.getElementById("sourcelist");
                                 try{
                                 for(i=0; i<list.length; i++)
                                 {
                                   if(list.options[i].selected)
                                   {
                                     encloseSelection(list.options[i].innerHTML,"");
                                     return false;
                                   }
                                 }
                                 }
                                 catch (e) {}
                                 return false;
                               };
    toolbar.appendChild(button);
  }

  function addList(id, title, fn){
    var list = document.createElement("select");
    list.id = id;
    list.title = title
    list.size = "1";
    var option = 0;
    for(i=0;i < sourcelists.length; i++)
    {
      option = document.createElement("option");
      option.innerHTML = sourcelists[i];
      if(i==0)
      {
        option.selected = "selected";
      }
      list.appendChild(option);
    }
    list.tabIndex = 400;
    toolbar.appendChild(list);
  }

    //copied from trac/htdocs/js/wikitoolbar.js
    function encloseSelection(prefix, suffix) {
      textarea.focus();
      var start, end, sel, scrollPos, subst;
      if (document.selection != undefined) {
        sel = document.selection.createRange().text;
      } else if (textarea.setSelectionRange != undefined) {
        start = textarea.selectionStart;
        end = textarea.selectionEnd;
        scrollPos = textarea.scrollTop;
        sel = textarea.value.substring(start, end);
      }
      if (sel.match(/ $/)) { // exclude ending space char, if any
        sel = sel.substring(0, sel.length - 1);
        suffix = suffix + " ";
      }
      subst = prefix + sel + suffix;
      if (document.selection != undefined) {
        var range = document.selection.createRange().text = subst;
        textarea.caretPos -= suffix.length;
      } else if (textarea.setSelectionRange != undefined) {
        textarea.value = textarea.value.substring(0, start) + subst +
                         textarea.value.substring(end);
        if (sel) {
          textarea.setSelectionRange(start + subst.length, start + subst.length);
        } else {
          textarea.setSelectionRange(start + prefix.length, start + prefix.length);
        }
        textarea.scrollTop = scrollPos;
      }
    }
 
  addList("sourcelist", "source_select", "");
  addInsertButton("insertbutton", "Insert_source", "");
    $(textarea).before(toolbar);
  }

})(jQuery);

// Add the toolbar to all <textarea> elements on the page with the class
// 'wikitext'.
jQuery(document).ready(function($) {
  $("textarea.wikitext").each(function() { addCodeReviewToolbar(this) });
});
</script>
<script type="text/javascript" src="<?cs
      var:htdocs_location ?>js/wikitoolbar.js"></script>
</form>
</div>


<?cs elif:page_class=='Save' ?>
<div class="wiki">
<?cs var:message ?>
</div>

<?cs /if ?>

<?cs include "footer.cs" ?>

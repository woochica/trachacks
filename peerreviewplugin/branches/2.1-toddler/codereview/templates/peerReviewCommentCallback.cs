<?cs if:invalid == 1 ?>
Invalid Parameters
<?cs /if ?>

<?cs if:invalid == 5 ?>
<html>
<head>
<script type="text/javascript" src="<?cs
  var:chrome.href ?>/hw/js/peerReviewCommentCallback.js"></script>
</head>
<body onload="top.timeToGetTree();" onunload="top.timeToHide(GLOBAL_line, GLOBAL_file, GLOBAL_parent);" style="background: #F7F7F7;" bottomMargin=0 topMargin=0 leftMargin=0 rightMargin=0>
  <table width="100%" id="addCommentTable">
    <tr>
      <td align="center">
        <textarea cols="31" rows="6" id="addCommentText"></textarea>
      </td>
    </tr>
    <tr height="3px">
      <td> </td>
    </tr>
    <tr>
      <td>&nbsp;&nbsp;Attach Code Sample <input type=checkbox onclick="showHideAttachFile();" value="Attach Code Sample" id="attachFileCheckbox"></td>
    </tr>
    <tr height="5px">
      <td> </td>
    </tr>
    <tr>
      <td align=right>
	<form action="<?cs var:trac.href.peerReviewCommentCallback ?>" method="post" id="HiddenCommentForm" name="HiddenCommentForm" enctype="multipart/form-data">
		<input type=hidden value="addComment" id="actionType" name="actionType">
		<input type=hidden value="" id="IDFile" name="IDFile">
		<input type=hidden value="" id="LineNum" name="LineNum">
		<input type=hidden value="" id="IDParent" name="IDParent">
		<input type=hidden value="" id="Text" name="Text">
		<input size="25" type=file value="" id="FileUp" name="FileUp" style="display:none;"><span id="FileUpCompanion" style="display:none;">&nbsp;</span>
	</form>
      </td>
    </tr>
    <tr>
      <td align="right" colspan="2" id="AddCommentButtonArea">
      </td>
    </tr>
  </table>
</body>
</html>
<?cs /if ?>

<?cs if:invalid == 2 ?>
Comment Text Blank
<?cs /if ?>

<?cs if:invalid == 3 ?>
Invalid Action Type
<?cs /if ?>

<?cs if:invalid == 4 ?>
Invalid Permission
<?cs /if ?>

<?cs if:invalid == 0 ?>
<?cs var:commentHTML ?>
<?cs /if ?>

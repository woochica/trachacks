<?cs if:invalid == 1 ?>
Invalid Parameters
<?cs /if ?>

<?cs if:invalid == 5 ?>
<html>
<head>
</head>
<body onload="top.timeToGetTree();" style="background: #F7F7F7;" bottomMargin=0 topMargin=0 leftMargin=0 rightMargin=0>
	<form action="<?cs var:trac.href.commentCallback ?>" method="post" id="HiddenCommentForm" name="HiddenCommentForm" enctype="multipart/form-data">
		<input type=hidden value="addComment" id="actionType" name="actionType">
		<input type=hidden value="" id="IDFile" name="IDFile">
		<input type=hidden value="" id="LineNum" name="LineNum">
		<input type=hidden value="" id="Text" name="Text">
		<input type=hidden value="" id="IDParent" name="IDParent">
		<div align=right>
			<input size="25" type=file value="" id="FileUp" name="FileUp">
		</div>
	</form>
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

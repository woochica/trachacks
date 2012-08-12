<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<style>
<!--
table.code th.addFileNums {
        width: 4em;
}
//-->
</style>

<!-- Top Navigation Bar -->
<div id="ctxtnav" class="nav"> 
	<h2>Peer Review Navigation</h2> 
	<ul>
		<li class="first">
			<?cs if:main == "yes" ?>My Code Reviews
			<?cs else ?><a href="<?cs var:trac.href.peerReviewMain ?>">My Code Reviews</a>
			<?cs /if ?>
		</li>
		<li>
			<?cs if:create == "yes" ?>Create a Code Review
			<?cs else ?><a href="<?cs var:trac.href.peerReviewNew ?>">Create a Code Review</a>
			<?cs /if ?>
		</li>
		<li <?cs if:manager == 0 ?>class="last"<?cs /if ?>>
			<?cs if:search == "yes" ?>Search Code Reviews
			<?cs else ?><a href="<?cs var:trac.href.peerReviewSearch ?>">Search Code Reviews</a>
			<?cs /if ?>
		</li>
		<?cs if:manager == 1 ?>
		<li class="last">
			<?cs if:option == "yes" ?>Manager Options
			<?cs else ?><a href="<?cs var:trac.href.peerReviewOptions ?>">Manager Options</a>
			<?cs /if ?>
		</li>
		<?cs /if ?>
	</ul> 
</div> 

<p><h1>Create a New Code Review</h1></p>

<h2>Step 1: Choose a name for this review.</h2><br>

<!-- CodeReview name is empty if new, with previous name is resubmitted -->
<form method="post" action="<?cs var:trac.href.peerReviewNew ?>" onsubmit="return validateInput(this);">
Name: <input type="text" name="Name" MAXLENGTH="50" value="<?cs var:name?>"><br>

<h2>Step 2: Select the sections to be reviewed.</h2><br>
<!-- Displays the file browser -->
<span id="browserArea"></span>
<table class="listing" id="myfilelist">
	<thead>
		<tr>
			<td>Filename (Click to remove)</td>
			<td>Start Line</td>
			<td>End Line</td>
			<td>Rev</td>
		</tr>
	</thead>

<!-- Display an empty file list if it's a new CodeReview, display previous list if resubmitted -->
	<tbody id = "myfilebody">
	<?cs if:new == "yes" ?>
		<tr id = "nofile" class="even">
			<td>No files have been added to the code review.</td>
			<td></td>
			<td></td>
			<td></td>
		</tr>
	<?cs else ?>
		<?cs each:item = prevFiles ?>
			<tr id="<?cs var:item[0] ?>,<?cs var:item[1] ?>,<?cs var:item[2] ?>,<?cs var:item[3] ?>id" class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
				<td value="<?cs var:item[0] ?>,<?cs var:item[1] ?>,<?cs var:item[2] ?>,<?cs var:item[3] ?>"><a href="javascript:removefile('<?cs var:item[0] ?>,<?cs var:item[1] ?>,<?cs var:item[2] ?>,<?cs var:item[3] ?>')"><?cs var:item[0] ?></a></td>
				<td><?cs var:item[2] ?></td>
				<td><?cs var:item[3] ?></td>
				<td><?cs var:item[1] ?></td>
			</tr>
		<?cs /each ?>
	<?cs /if ?>
	</tbody>
</table><br><br>

<h2>Step 3: Select reviewers for your review.</h2><br>

<!-- Display a full reviewer drop-down list if it's a new CodeReview, display unassigned reviewers if resubmitted -->
<?cs if:new == "yes" ?>
	<select id="Reviewers">
		<?cs each:item = users ?>
			<option value="<?cs var:item ?>"><?cs var:item ?></option>
		<?cs /each ?>
	</select>
<?cs else ?>
	<?cs if:emptyList == 0 ?>
		<select id="Reviewers">
			<?cs each:item = notPrevUsers ?>
				<option value="<?cs var:item ?>"><?cs var:item ?></option>
			<?cs /each ?>
		</select>
	<?cs else ?>
		<select id="Reviewers">
				<option value="-1">--All users exhausted--</option>
		</select>
	<?cs /if ?>
<?cs /if ?>

<input <?cs if:emptyList==1 ?>disabled<?cs /if ?> id="adduserbutton" type="button" onclick="adduser()" value="Add user"><br>

<!-- Display an empty file list if it's a new CodeReview, display previous list if resubmitted -->
<?cs if:new == "yes" ?>
		<table class="listing" id="myuserlist">
		<thead>
			<tr>
				<td>Username (Click to remove)</td>
			</tr>
		</thead>
		<tbody id = "myuserbody">
			<tr id = "No Users" class="even">
				<td>No users have been added to the code review.</td>
			</tr>
		</tbody>
	</table>
<?cs else ?>
	<table class="listing" id="myuserlist">
		<thead>
			<tr>
				<td>Username (Click to remove)</td>
			</tr>
		</thead>
		<tbody id = "myuserbody">
			<?cs each:item = prevUsers ?>
				<tr id="<?cs var:item ?>id" class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
					<td value="<?cs var:item ?>"><a href="javascript:removeuser('<?cs var:item ?>')"><?cs var:item ?></a></td>
				</tr>
			<?cs /each ?>
		</tbody>
	</table>
<?cs /if ?>
<br><br>

<h2>Step 4: Write general notes and instructions for the reviewers. (Optional)</h2>
<!-- Display an empty notes area if it's a new CodeReview, display previous notes if resubmitted -->
	<textarea name="Notes" cols=60 rows=8><?cs if:new != "yes" ?><?cs var:notes ?><?cs /if ?></textarea>

<br><br>
<?cs if:oldid > -1 ?>
<input type="hidden" name="oldid" value="<?cs var:oldid ?>">
<?cs /if ?>
<input type="hidden" name="ReviewersSelected" id="ReviewersSelected" value="<?cs if:new != "yes" ?><?cs var:reviewers ?><?cs /if ?>">
<input type="hidden" name="FilesSelected" id="FilesSelected" value="<?cs if:new != "yes" ?><?cs var:files ?><?cs /if ?>">
<input type="hidden" name="reqAction" value="createCodeReview">
<input type="submit" name="Next" value="<?cs if:new == "yes" ?>Add Code Review<?cs else ?>Resubmit Code Review<?cs /if ?>">
<br>
</form>

<script type="text/javascript">
<!--
var browserCallback = "<?cs var:trac.href.peerReviewBrowser ?>";
//-->
</script>
<script type="text/javascript" src="<?cs
  var:chrome.href ?>/hw/js/peerReviewNew.js"></script>

<?cs include "footer.cs" ?>

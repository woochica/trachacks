<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

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
			<?cs if:options == "yes" ?>Manager Options
			<?cs else ?><a href="<?cs var:trac.href.peerReviewOptions ?>">Manager Options</a>
			<?cs /if ?>
		</li>
		<?cs /if ?>
	</ul> 
</div> 

<p><b><h1>Manager Options</h1></b></p>

<form method="post" action="<?cs var:trac.href.peerReviewOptions ?>" id="thresholdForm">
<p>Voting threshold: <input type="text" size="1" maxlength="3" name="percentage" value="<?cs var:percentage ?>">%
<br>
<input type="button" name="set" value="Set Threshold" onclick="validateInput();"><p>
<p><?cs if:success == 1 ?>The Threshold has been successfuly updated.<?cs /if ?><p>

<p> This setting defines the number of positive votes versus total votes necessary for an author to submit for a manager's approval
</form>

<script type="text/javascript">
<!--

//Ensure a correct percentage is input
function validateInput() {
	var form = document.getElementById('percentage');
    var val = parseInt(form.value);
    val != form.value-0
    if (val != form.value-0 || (val < 0) || (val > 100)) {
        alert("You must specify an integer percentage between 0 and 100.");
		return false;
    } else {
    	document.getElementById('thresholdForm').submit();
    }
}
//-->
</script>
<?cs include "footer.cs" ?>

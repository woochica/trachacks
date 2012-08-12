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
			<?cs if:option == "yes" ?>Manager Options
			<?cs else ?><a href="<?cs var:trac.href.peerReviewOptions ?>">Manager Options</a>
			<?cs /if ?>
		</li>
		<?cs /if ?>
	</ul> 
</div> 

<p><h1>Code Review Details</h1></p>

Code review name: <?cs var:name?><br>
Code review status: <?cs var:status?><br>
Author:  <?cs var:author?><br>
Creation Date:  <?cs var:datecreate?><br>
<br>




<script type="text/javascript">

function handlerowclick(num){
    
}

</script>



<h2>Files associated with this code review</h2>
<table class="listing" id="filelist">
    <thead>
        <tr>
            <td>File ID</td>
            <td>Filename</td>
            <td>Revision</td>
            <td>Line Numbers</td>
        </tr>
    </thead>
    <tbody>
        <?cs if:filesLength == 0?>
            <tr class="even">
                <td>There are no files included in this code review.</td>
            </tr>
        <?cs else ?>
            <?cs each:item = files ?>
                <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
                    <td><a href="<?cs var:trac.href.peerReviewPerform ?>?IDFile=<?cs var:item[0]?>"><?cs var:item[0]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewPerform ?>?IDFile=<?cs var:item[0]?>"><?cs var:item[2]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewPerform ?>?IDFile=<?cs var:item[0]?>"><?cs var:item[5]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewPerform ?>?IDFile=<?cs var:item[0]?>"><?cs var:item[3]?>-<?cs var:item[4]?></a></td>
                </tr>
            <?cs /each ?>
        <?cs /if ?>
    </tbody>
</table>

<br>


<h2>Users assigned to this code review</h2>
<?cs if:author==myname || manager==1 ?>
<table class="listing" id="userlist">
    <thead>
        <tr>
            <td>User name</td>
            <td>Vote</td>
        </tr>
    </thead>
    <tbody>
        <?cs if:rvsLength == 0?>
            <tr class="even">
                <td>There are no users included in this code review.</td>
            </tr>
        <?cs else?>
            <?cs each:item = rvs ?>
                <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
                    <td><?cs var:item[0]?></td>
                    <td><?cs var:item[1]?></td>
                </tr>
            <?cs /each ?>
        <?cs /if ?>
    </tbody>
</table>
<?cs else ?>
<table class="listing" id="userlist">
    <thead>
        <tr>
            <td>User name</td>
        </tr>
    </thead>
    <tbody>
        <?cs if:rvsLength == 0?>
            <tr class="even">
                <td>There are no users included in this code review.</td>
            </tr>
        <?cs else?>
            <?cs each:item = rvs ?>
                <tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
                    <td><?cs var:item[0]?></td>
                </tr>
            <?cs /each ?>
        <?cs /if ?>
    </tbody>
</table>
<?cs /if ?>

<br><br>
<h2>Author's notes and instructions</h2>
<textarea name="Notes" cols=60 rows=8 readonly><?cs var:notes ?></textarea>
<br><br>

<?cs if:viewvotesummary == 1 ?>

<h2>Vote summary</h2>
<table width = "35%">
    <tr>
        <td><b>Vote tally:</td>
        <td><font color = limegreen><b>Yes: <?cs var:voteyes?></b></font></td>
        <td><font color = red><b>No: <?cs var:voteno?></b></font></td>
        <td><b>Pending: <?cs var:notvoted?></b></td>
    </tr>
    <?cs if:canivote == 1 ?>
    <tr>
	  <td><b>Your vote is:</b></td>
	  <td><b><?cs if:myvote == -1?>
				Pending
			<?cs elif:myvote == 0?>
				<font color = red>No</font>
			<?cs elif:myvote == 1?>
				<font color = limegreen>Yes</font>
			<?cs /if ?></b></td>
    </tr>
    <?cs /if ?>
</table>
<br>
<br>
<?cs /if ?>

<?cs if:canivote == 1 && status != "Closed" && status !=  "Ready for inclusion" ?>
<h2><?cs if:myvote != -1 ?>Modify<?cs else?>Cast<?cs /if?> your vote:</h2>
<table>
    <tr>
        <td>
            <form method="post" action="<?cs var:trac.href.peerReviewView ?>">
            <input type="submit" value="Approve">
		<input type="hidden" value="<?cs var:reviewID ?>" name="Review">
		<input type="hidden" value="yes" name="Vote">
            </form>
        </td>
        <td>
            <form method="post" action="<?cs var:trac.href.peerReviewView ?>">
            <input type="submit" value="Not Approve">
		<input type="hidden" value="<?cs var:reviewID ?>" name="Review">
		<input type="hidden" value="no" name="Vote">
            </form>
        </td>
    </tr>
</table>
<?cs /if ?>

<?cs if:manager==1 ?>
<h2>Manager privileges</h2>
Change code review status:
<table valign="middle">
    <tr>
        <td>
            <form method="post" action="<?cs var:trac.href.peerReviewView ?>">
                <select name="ManagerChoice" id="ManagerChoice">
                    <option value="Open for review">Open for review</option>
                    <option value="Reviewed">Reviewed</option>
                    <option value="Ready for inclusion">Ready for inclusion</option>
                    <option value="Closed">Closed</option>
                </select>
		    	<input type="hidden" value="<?cs var:reviewID ?>" name="Review">
		    	<input type="submit" name="submitbutton" value="Change Status">
            </form>
         </td>
        <td width = 30px></td>
        <td>
            <form method="post" action="<?cs var:trac.href.peerReviewNew ?>">
            <input type="submit" value="Resubmit For Review">
		<input type="hidden" value="<?cs var:reviewID?>" name="resubmit">
            </form>
        </td>
    <tr>
</table>  
<?cs elif:author == myname ?>
<h2>Author privileges</h2>
<table>
	<tr>
		<?cs if:status != "Ready for inclusion" && status != "Closed" ?>
		<td>
			<form method="post" action="<?cs var:trac.href.peerReviewView ?>">
			<input type="submit" value="Submit For Inclusion" <?cs if:status != "Reviewed" ?>disabled=true<?cs /if ?>>
			<input type="hidden" value="<?cs var:reviewID?>" name="Review">
			<input type="hidden" value="1" name="Inclusion">
			</form>
		</td>
		<?cs /if ?>
		<td>
            	<form method="post" action="<?cs var:trac.href.peerReviewNew ?>">
            		<input type="submit" value="Resubmit For Review">
				<input type="hidden" value="<?cs var:reviewID?>" name="resubmit">
			</form>
		</td>
        <?cs if:status != "Closed" ?>
		<td>
			<form method="post" action="<?cs var:trac.href.peerReviewView ?>">
				<input type="submit" value="Close This Code Review">
				<input type="hidden" value="1" name="Close">
				<input type="hidden" value="<?cs var:reviewID?>" name="Review">
			</form>
		</td>
		<?cs /if ?>
	</tr>
</table>
<?cs /if ?>

<?cs include "footer.cs" ?>

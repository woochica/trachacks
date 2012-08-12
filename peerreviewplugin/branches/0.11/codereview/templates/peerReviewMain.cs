<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<!-- Top navigation bar -->
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


<p><h1>My Code Reviews</h1></p>

<br>
<!-- If we are a manager, display a table containing all of the code reviews requiring your approval. -->
<?cs if:author == "manager" ?>
<p><h2>This is a list of the code reviews currently requiring your approval.</h2></p>
<table class="listing" id="approvereviewlist">
	<thead>
		<tr>
			<td>Review</td>
			<td>Author</td>
			<td>Name</td>
			<td>Date Opened</td>
		</tr>
	</thead>
	<tbody>
        <!-- if there are no reviews open for you, state this in the table -->
        <?cs if: (managerReviewArrayLength == 0) ?>
			<tr>		
			<td>There are no code reviews requiring your approval.</td>
			<td></td>
			<td></td>
			<td></td>
			</tr>
		<?cs else ?>
			<?cs each:item = managerReviews ?>
				<tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
                    <!-- Set up the table with the appropriate values and then links to view the review -->
               		<td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[0]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[1]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[2]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[3]?></a></td>
				</tr>
			<?cs /each ?>
		<?cs /if ?>
		
	</tbody>
</table>
<br>
<br>
<?cs /if ?>

<p><h2>This is a list of your currently open code reviews.</h2></p>

<!-- Display your currently open code reviews in a table -->
<table class="listing" id="myreviewlist">
	<thead>
		<tr>
			<td>Review</td>
			<td>Name</td>
			<td>Status</td>
			<td>Date Opened</td>
		</tr>
	</thead>
	<tbody>
		<!-- if there are no reviews open for you, state this in the table -->
		<?cs if:(reviewReturnArrayLength == 0) ?>
			<tr>
			<td>Your have no code reviews currently open.</td>
			<td></td>
			<td></td>
			<td></td>
			</tr>
		<?cs else ?>
			<?cs each:item = myCodeReviews ?>
				<tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
                    <!-- Set up the table with the appropriate values and then links to view the review -->
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[0]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[4]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[2]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[3]?></a></td>
				</tr>
			<?cs /each ?>
		<?cs /if ?>
	</tbody>
</table>

<br>
<br>
<p><h2>This is a list of code reviews currently assigned to you.</h2></p>

<!-- Display your currently assigned code reviews in a table -->
<table class="listing" id="assignedreviewlist">
	<thead>
		<tr>
			<td>Review</td>
			<td>Author</td>
			<td>Name</td>
			<td>My Vote</td>
			<td>Date Opened</td>
		</tr>
	</thead>
	<tbody>
        <!-- if there are no reviews open for you, state this in the table -->
        <?cs if: (assignedReturnArrayLength == 0) ?>
			<tr>
			<td>There are no code reviews assigned to you.</td>
			<td></td>
			<td></td>
			<td></td>
			<td></td>
			</tr>
		
		<?cs else ?>
			<?cs each:item = assignedReviews ?>
				<tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
                    <!-- Set up the table with the appropriate values and then links to view the review -->
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[0]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[1]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[2]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[4]?></a></td>
                    <td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[3]?></a></td>
				</tr>
			<?cs /each ?>
		<?cs /if ?>
	</tbody>
</table>
<br>
<br>

<?cs include "footer.cs" ?>

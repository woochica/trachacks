<?cs include "discussion-header.cs" ?>

<h1>Forum Index</h1>
<table>
	<tr>
		<th class="subject">Forum</th>
		<th class="topics">Topics</th>
		<th class="messages">Replies</th>
	</tr>
	<?cs each:forum = discussion.forums ?>
		<tr>
			<td class="subject">
				<a href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>">
					<div class="subject"><?cs var:forum.subject ?></div>
					<div class="description"><?cs var:forum.description ?></div>
				</a>
			</td>
			<td class="topics"><a href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>"><div class="topics"><?cs var:forum.topics ?></div></a></td>
			<td class="messages"><a href="<?cs var:trac.href.discussion ?>/<?cs var:forum.name ?>"><div class="messages"><?cs var:forum.replies ?></div></a></td>
		</tr>
	<?cs /each ?>
</table>

<?cs include "discussion-footer.cs" ?>

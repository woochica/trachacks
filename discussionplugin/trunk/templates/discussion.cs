<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
 <h2>Wiki Navigation</h2>
 <ul>
	<?cs if:discussion.forum.name ?>
		<?cs if:discussion.topic.id ?>
			<li><a href="<?cs var:trac.href.discussion ?>">Forum Index</a></li>
			<?cs if:discussion.message.id ?>
				<li><a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>"><?cs var:discussion.forum.subject ?></a></li>
				<li class="last"><a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:discussion.topic.id ?>"><?cs var:discussion.topic.subject ?></a></li>
			<?cs else ?>
				<li class="last"><a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>"><?cs var:discussion.forum.subject ?></a></li>
			<?cs /if ?>
		<?cs else ?>
			<li class="last"><a href="<?cs var:trac.href.discussion ?>">Forum Index</a></li>
		<?cs /if ?>
  <?cs /if ?>
 </ul>
 <hr />
</div>

<div id="content" class="discussion">
<div id="<?cs var:discussion.mode ?>" class="<?cs var:discussion.mode ?>">

<?cs if:discussion.mode == "forum-list" ?>
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
<?cs elif:discussion.mode == "topic-list" ?>
	<h1><?cs var:discussion.forum.subject ?></h1>
	<div class="forum-description"><?cs var:discussion.forum.description ?></div>
	<table>
		<tr>
			<th class="subject">Subject</th>
			<th class="author">Author</th>
			<th class="messages">Replies</th>
		</tr>
		<?cs each:topic = discussion.topics ?>
			<tr>
				<td class="subject"><a class="subject" href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>"><?cs var:topic.subject ?></a></td>
				<td class="author"><a class="author" href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>"><?cs var:topic.author ?></a></td>
				<td class="messages"><a class="messages" href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:topic.id ?>"><?cs var:topic.replies ?></a></td>
			</tr>
		<?cs /each ?>
	</table>
	<form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>">
		<input type="submit" name="newtopic" value="New Topic"/>
	</form>
<?cs elif:discussion.mode == "message-list" ?>
	<?cs def:display_topic(messages) ?>
		<?cs each:message = messages ?>
			<li>
				<div class="body"><?cs var:message.body ?></div>
				<div class="controls"><a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:discussion.topic.id ?>?reply=<?cs var:message.id ?>">reply</a></div>
				<div class="author"><?cs var:message.author ?></div>
			</li>
			<?cs if:message.replies.0.body || message.id == args.reply ?>
				<ul>
					<?cs call:display_topic(message.replies) ?>
					<?cs if:message.id == args.reply ?>
						<li class="reply">
							<form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:discussion.topic.id ?>">
								<textarea style="height: 10em; width: 98%; "></textarea>
								<input type="hidden" name="reply" value="<?cs var:args.reply ?>/"/>
								<input type="submit" name="preview" value="Preview"/>
								<input type="submit" name="reply" value="Reply"/>
								<input type="submit" name="cancel" value="Cancel"/>
							</form>
						</li>
					<?cs /if ?>
				</ul>
			<?cs /if ?>
		<?cs /each ?>
	<?cs /def ?>
	
	<h1 class="forum-subject"><?cs var:discussion.forum.subject ?></h1>
	<div class="topic">
		<div class="header">
			<div class="subject"><?cs var:discussion.topic.subject ?></div>
			<div class="body"><?cs var:discussion.topic.body ?></div>
			<div class="controls"><a href="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:discussion.topic.id ?>?reply=0">reply</a></div>
			<div class="author"><?cs var:discussion.topic.author ?></div>
		</div>
		<?cs if:args.reply || discussion.messages.0.author ?>
			<div class="replies">
				<ul>
					<?cs call:display_topic(discussion.messages) ?>
					<?cs if:args.reply && args.reply == 0 ?>
						<li class="reply">
							<form method="post" action="<?cs var:trac.href.discussion ?>/<?cs var:discussion.forum.name ?>/<?cs var:discussion.topic.id ?>">
								<textarea style="height: 10em; width: 98%; "></textarea>
								<input type="hidden" name="reply" value="<?cs var:args.reply ?>/"/>
								<input type="submit" name="preview" value="Preview"/>
								<input type="submit" name="reply" value="Reply"/>
								<input type="submit" name="cancel" value="Cancel"/>
							</form>
						</li>
					<?cs /if ?>
				</ul>
			</div>
		<?cs /if ?>
	</div>
<?cs /if ?>

</div>
</div>

<?cs include "footer.cs" ?>

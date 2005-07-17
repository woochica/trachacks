<?cs include "discussion-header.cs" ?>

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

<?cs include "discussion-footer.cs" ?>

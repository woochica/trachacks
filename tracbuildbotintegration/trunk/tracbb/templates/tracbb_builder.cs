<?cs include "tracbb_header.cs"?>
<div id="content">
<h1><a href="<?cs var:buildbot.url?>/builders/<?cs var:bb.builder?>"><?cs var:bb.builder ?></a> Status Page</h1>
<h2>Builders</h2>
<?cs each:build = bb.builds ?>
<p>
<?cs if:build.status == "success" ?>
	<img src="<?cs var:chrome.href ?>/tracbb/bbsuccess.png" border="0"/> 
<?cs else ?>
	<img src="<?cs var:chrome.href ?>/tracbb/bberror.png" border="0"/> 
<?cs /if ?>
<a href="<?cs var:build.url ?>">build #<?cs var:build.number ?></a>
</p>
<?cs /each ?>
</div>
<?cs include "footer.cs"?>

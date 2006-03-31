<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
 <h2>Wiki Navigation</h2>
 <ul>
  <li><a href="<?cs var:trac.href.wiki ?>">Start Page</a></li>
  <li><a href="<?cs var:trac.href.wiki ?>/TitleIndex">Title Index</a></li>
  <li><a href="<?cs var:trac.href.wiki ?>/RecentChanges">Recent Changes</a></li>
  <?cs if:wiki.history_href ?>
   <li class="last"><a href="<?cs var:wiki.history_href ?>">Page History</a></li>
  <?cs else ?>
   <li class="last">Page History</li>
  <?cs /if ?>
 </ul>
 <hr />
</div>

<div id="content" class="wiki">
   <div class="wikipage">
    <div id="searchable">
    <?cs each:bentry = blog.entries ?>
        <p><?cs var:bentry.wiki_text ?></p>
        <div class="nav">
            <ul>
                <li><?cs var:bentry.wiki_link ?></li>
                <li><?cs var:bentry.author ?></li>
                <li><?cs var:bentry.time ?></li>
            </ul>
        </div>
        <hr width="75%" />
    <?cs /each ?>
    </div>
   </div>
  <script type="text/javascript">
   addHeadingLinks(document.getElementById("searchable"));
  </script>
  <?cs if wiki.action == "view" ?>
  <?cs /if ?>
</div>

<?cs include "footer.cs" ?>

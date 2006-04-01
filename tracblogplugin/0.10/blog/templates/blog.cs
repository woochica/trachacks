<?cs if ! blog.macro ?>
    <?cs include "header.cs" ?>
    <?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
    <h2>Wiki Navigation</h2>
    <ul>
        <li><a href="<?cs var:trac.href.blog ?>/new">New Blog Entry</a></li>
        <li><a href="<?cs var:trac.href.wiki ?>">Start Page</a></li>
        <li><a href="<?cs var:trac.href.wiki ?>/TitleIndex">Title Index</a></li>
        <li><a 
            href="<?cs var:trac.href.wiki ?>/RecentChanges">Recent Changes</a>
        </li>
    </ul>
    <hr />
</div>

<div id="content" class="wiki">
   <div class="wikipage">
    <div id="searchable">
<?cs /if ?>

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

<?cs if ! blog.macro ?>
    </div>
   </div>
  <script type="text/javascript">
   addHeadingLinks(document.getElementById("searchable"));
  </script>
</div>

<?cs include "footer.cs" ?>
<?cs /if ?>

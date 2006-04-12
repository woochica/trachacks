<?cs if ! blog.macro ?>
    <?cs include "header.cs" ?>
    <?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
    <h2>Wiki Navigation</h2>
    <ul>
        <?cs if trac.acl.BLOG_POSTER ?>
        <li><a href="<?cs var:trac.href.blog ?>/new"><?cs var:blog.newblog ?></a></li>
        <?cs /if ?>
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

<?cs include:"blog_calendar.cs" ?>

<?cs if ! 1 ?>
<div class="blognav">
    This is some navigation things
    <ul>Posts Per Month:
        <li>March (7)</li>
    </ul>
</div>
<?cs /if ?>

<div class="blog">
    <?cs each:bentry = blog.entries ?>
    <div class="post">
        <p><?cs var:bentry.wiki_text ?></p>
        <?cs if bentry.modified ?>
            <div class="updated">
                <p>Updated on <?cs var:bentry.mod_time ?></p>
            </div>
        <?cs /if ?>
        <div class="postmeta">
            <ul>
                <li><?cs var:bentry.wiki_link ?></li>
                <li><?cs var:bentry.author ?></li>
                <li class="last"><?cs var:bentry.time ?></li>
            </ul>
        </div>
        <?cs if !  bentry.last ?>
            <hr width="75%" />
        <?cs /if ?>
    </div>
    <?cs /each ?>
</div>

<?cs if ! blog.macro ?>
    </div>
   </div>
  <script type="text/javascript">
   addHeadingLinks(document.getElementById("searchable"));
  </script>
</div>

<?cs include "footer.cs" ?>
<?cs /if ?>

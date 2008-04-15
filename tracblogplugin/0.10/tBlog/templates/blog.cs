<?cs if ! blog.macro ?>
    <?cs include "header.cs" ?>
    <?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
    <h2>Wiki Navigation</h2>
    <ul>
        <?cs if trac.acl.BLOG_POSTER ?>
        <li><a href="<?cs var:trac.href.blog ?>/new"><?cs var:blog.newblog ?></a></li>
        <?cs /if ?>
    </ul>
    <hr />
</div>

<div id="content" class="wiki">
   <div class="wikipage">
    <div id="searchable">
    <?cs var:blog.header ?>
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
                <?cs if bentry.tags.present != 0 ?>
                <li>Posted in: <?cs each:tag=bentry.tags.tags ?><a href="<?cs if cgi_location != "/" ?><?cs var:cgi_location ?><?cs /if ?>/tags/<?cs var:tag.link ?>"><?cs var:tag.name ?></a><?cs if ! tag.last ?>,<?cs /if ?> <?cs /each ?> <?cs if bentry.tags.more ?><a href="<?cs var:trac.href.wiki ?>/<?cs var:bentry.name ?>">...</a><?cs /if ?>
                <?cs /if ?>
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
   addHeadingLinks(document.getElementById("searchable"), "Link to this section");
  </script>
</div>

<?cs include "footer.cs" ?>
<?cs /if ?>

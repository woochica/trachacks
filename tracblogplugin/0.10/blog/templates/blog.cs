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

<!-- Quicklogs summary calendar -->
<?cs def:cal_link(year, month, day) ?><?cs var:blog.path_info ?>?year=<?cs var:year ?>&month=<?cs var:month ?>&day=<?cs var:day ?><?cs /def ?>
<div class="blog-calendar">
    <table>
        <tr>
            <td><a href="<?cs call:cal_link(blog.date.lastyear,blog.date.month,blog.date.day) ?>">&lt;&lt;</a></td>
            <td><a href="<?cs call:cal_link(blog.date.lastmonth.year,blog.date.lastmonth.month,blog.date.day) ?>">&lt;</a></td>
            <td colspan="3" align="center"><?cs var:blog.date.monthname ?> <?cs var:string.slice(blog.date.year,2,4)?></td>
            <td><a href="<?cs call:cal_link(blog.date.nextmonth.year,blog.date.nextmonth.month,blog.date.day)?>">&gt;</a></td>
            <td><a href="<?cs call:cal_link(blog.date.nextyear,blog.date.month,blog.date.day) ?>">&gt;&gt;</a></td>
        </tr>
        <tr>
        <?cs each:name = blog.date.daynames ?>
            <td><?cs var:name ?></td>
        <?cs /each ?>
        </tr>
        <?cs each:week = blog.cal ?>
        <tr <?cs if:name(week)==blog.date.week ?>
            class="blog-calendar-current" <?cs /if ?>>
            <?cs each:day = week ?>
            <td <?cs if:day==blog.date.day ?>class="blog-calendar-current"<?cs /if ?>>
            <?cs if:day ?>
            <a href="<?cs call:cal_link(blog.date.year, blog.date.month, day) ?>"><?cs var:day ?></a>
            <?cs else ?>&nbsp;<?cs /if ?>
            </td>
            <?cs /each ?>
        </tr>
        <?cs /each ?>
    </table>
</div>

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
        <hr width="75%" />
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

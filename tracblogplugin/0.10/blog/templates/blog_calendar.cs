<?cs if ! blog.hidecal ?>
<!-- Calendar gratefully donate from coderanger -->
<?cs def:day_link(year, month, day) ?><?cs var:blog.path_info ?>?year=<?cs var:year ?>&month=<?cs var:month ?>&day=<?cs var:day ?><?cs /def ?>
<?cs def:mon_link(year, month) ?><?cs var:blog.path_info ?>?year=<?cs var:year ?>&month=<?cs var:month ?><?cs /def ?>
<div class="blog-calendar">
    <table>
        <tr>
            <td><a href="<?cs call:mon_link(blog.date.lastyear,blog.date.month) ?>">&lt;&lt;</a></td>
            <td><a href="<?cs call:mon_link(blog.date.lastmonth.year,blog.date.lastmonth.month) ?>">&lt;</a></td>
            <td colspan="3" align="center"><a href="<?cs call:mon_link(blog.date.year,blog.date.month) ?>"><?cs var:blog.date.monthname ?></a> <?cs var:string.slice(blog.date.year,2,4)?></td>
            <td><a href="<?cs call:mon_link(blog.date.nextmonth.year,blog.date.nextmonth.month)?>">&gt;</a></td>
            <td><a href="<?cs call:mon_link(blog.date.nextyear,blog.date.month) ?>">&gt;&gt;</a></td>
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
            <a href="<?cs call:day_link(blog.date.year, blog.date.month, day) ?>"><?cs var:day ?></a>
            <?cs else ?>&nbsp;<?cs /if ?>
            </td>
            <?cs /each ?>
        </tr>
        <?cs /each ?>
    </table>
</div>
<?cs /if ?>

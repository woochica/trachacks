<?cs if ! blog.hidecal ?>
<!-- Calendar gratefully donate from coderanger -->
<?cs def:day_link(year, month, day) ?><?cs var:blog.path_info ?>?year=<?cs var:year ?>&month=<?cs var:month ?>&day=<?cs var:day ?><?cs /def ?>
<?cs def:mon_link(year, month) ?><?cs var:blog.path_info ?>?year=<?cs var:year ?>&month=<?cs var:month ?><?cs /def ?>
<?cs def:year_link(year) ?><?cs var:blog.path_info ?>?year=<?cs var:year ?><?cs /def ?>
<div class="blog-calendar">
    <table cellspacing="0" cellpadding="0">
        <caption class="blog-calendar-caption">
            <a href="<?cs call:mon_link(blog.date.lastyear,blog.date.month) ?>">&lt;&lt;</a>&nbsp;
            <a href="<?cs call:mon_link(blog.date.lastmonth.year,blog.date.lastmonth.month) ?>">&lt;</a>&nbsp;
            <a class="blog-calendar-title" 
            title="<?cs var:blog.date.monthcount ?> Post(s)"
            href="<?cs call:mon_link(blog.date.year,blog.date.month) ?>"><?cs var:blog.date.monthname ?></a>&nbsp;
            <a class="blog-calendar-title"
            title="<?cs var:blog.date.yearcount ?> Post(s)"
            href="<?cs call:year_link(blog.date.year) ?>"><?cs var:blog.date.year ?></a>&nbsp;
            <a href="<?cs call:mon_link(blog.date.nextmonth.year,blog.date.nextmonth.month)?>">&gt;</a>&nbsp;
            <a href="<?cs call:mon_link(blog.date.nextyear,blog.date.month) ?>">&gt;&gt;</a>
        </caption>
        <thead>
            <tr align="center" class="blog-calendar-header">
            <?cs each:name = blog.date.daynames ?>
                <th class="blog-calendar-header" scope="col"><b><?cs var:name ?></b></th>
            <?cs /each ?>
            </tr>
        </thead>
        <tbody>
            <?cs each:week = blog.cal ?>
            <tr align="right" <?cs if:week.num==blog.date.week ?>
                class="blog-calendar-current" <?cs /if ?>>
                <?cs each:day = week.days ?>
                <td <?cs if:day.num==blog.date.day ?>class="blog-calendar-current"<?cs /if ?>>
                <?cs if:day.num ?>
                <a <?cs if:day.count <= 0 ?>class="missing"<?cs /if ?>
                title="<?cs var:day.count ?> Post(s)"
                href="<?cs call:day_link(blog.date.year, blog.date.month, day.num) ?>"><?cs var:day.num ?></a>
                <?cs else ?>&nbsp;<?cs /if ?>
                </td>
                <?cs /each ?>
            </tr>
        </tbody>
        <?cs /each ?>
    </table>
</div>
<?cs /if ?>

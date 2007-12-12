<?cs def:sortable_th(order, desc, class, title, href) ?>
 <th class="<?cs var:class ?><?cs if:order == class ?> <?cs
   if:desc ?>desc<?cs else ?>asc<?cs /if ?><?cs /if ?>">
  <a title="Sort by <?cs var:class ?><?cs
    if:order == class && !desc ?> (descending)<?cs /if ?>" href="<?cs
    var:href ?>&amp;order=<?cs var:class ?><?cs
    if:order == class && !desc ?>&amp;desc=1<?cs /if ?>"><?cs var:title ?></a>
 </th><?cs
/def ?><?cs 
include:"downloads_cntx_nav.cs" ?>
<h2>Downloader stats admin</h2>
<div id="per_page">
    <form method="post">
        <label>Per page: 
        <input type="text" name="per_page" value="<?cs var:stats.per_page ?>" class="in_txt"/>
        </label>
        <input type="submit" name="per_page_submit" value="Show" />
    </form>
</div>
<div id="page_list">
<?cs if:subcount(stats.pg_lst) > 1 ?>Pages: <?cs 
    each:pg = stats.pg_lst 
    ?><?cs if:stats.pg_act!=pg.1  ?><a href="<?cs var:pg.0 ?>"><?cs var:pg.1 ?></a><?cs 
    else ?><strong><?cs var:pg.1 ?></strong><?cs /if ?> <?cs
    /each?><?cs else ?>&nbsp;<?cs /if ?>
</div>
<table class="listing wide">
  <thead>
    <tr><?cs
      each:th = stats.head ?><?cs
        if:!th.2 ?>
            <th><?cs var:th.1 ?></th><?cs
        else ?><?cs 
            call:sortable_th(stats.order, stats.desc, th.0, th.1, href.full+'/?') 
        ?><?cs 
        /if ?><?cs
      /each 
    ?></tr>
  </thead><?cs set:row_num=1 ?><?cs 
  each:row = stats.rows ?><?cs 
    if row_num % #2 ?><?cs 
      set:row_class = 'even' ?><?cs 
    else ?><?cs 
      set:row_class = 'odd' ?><?cs 
    /if ?>
  <tr class="<?cs var:row_class ?>"><?cs
    each:item = stats.head ?>
      <td class="thin<?cs 
                    if:item.0=='timestamp' ?> tms<?cs
                    elif:item.0=='id' ?> id<?cs
                    elif:item.0=='actions' ?> act<?cs 
                    /if ?>"><?cs 
        var:row[item.0] ?></td><?cs 
    /each ?><?cs set:row_num = row_num + 1 ?>
    </tr><?cs 
  /each ?>
</table>
<div id="del_range">
    <form method="post">
        Delete range of records -
        <label> start
        <input type="text" name="start" value="" />
        </label>
        <label>end
        <input type="text" name="end" value="" />
        </label>
        <input type="submit" name="del_range_submit" value="Delete" /><br/>
        Format must be: <?cs var:datetime_hint ?> <br/>Use this carefully and first check sorting of data (should be by timestamp).
    </form>
</div>


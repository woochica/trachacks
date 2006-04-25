<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="content" class="pagelist">
 <h1>PageList!</h1>
 <?cs each:page = pagelist.pages ?>
   <a href="<?cs var:page.prefix ?>/<?cs var:page.name ?>"><?cs var:page.name ?></a><br/>
 <?cs /each ?>
</div>

<?cs include "footer.cs" ?>

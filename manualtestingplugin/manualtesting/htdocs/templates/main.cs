<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
   <h2>Suite Navigation</h2>
    <ul>
        <li class="first">
            <?cs if:chrome.links.up.0.href ?>
                <a href="<?cs var:chrome.links.up.0.href ?>">Available Test Suites</a>
            <?cs else ?>Available Test Suites
            <?cs /if ?>
        </li>
    </ul>
</div>

<div id="content" class="suites">
    <h1>Available Test Suites</h1>
    <p>This is a list of test suites available.</p>
    <?cs if:manualtesting.suites.0.title ?>
    <table class="listing">
        <thead>
            <tr>
                <!--
                columns = ('id','title','description','component','deleted','user')
                -->
                <th><a href="#" title="">Report</a></th>
                <th><a href="#" title="">Title</a></th>
                <th><a href="#" title="">Component</a></th>
                <th><a href="#" title="">Description</a></th>
            </tr>
        </thead>
        <tbody>
            <?cs set idx = #0 ?>
            <?cs each:row = manualtesting.suites ?>
                <?cs set idx = idx + #1 ?>
                <?cs if:row.title ?>
                    <?cs if idx % #2 ?>
                        <tr class="even">
                    <?cs else ?>
                        <tr class="odd">
                    <?cs /if ?>
                            <td class="report">
                                <a href="/trac/testing/<?cs var:row.id ?>" title="View Suite">
                                    <?cs var:row.id ?>
                                </a>
                            </td>
                            <td class="title">
                                <a href="/trac/testing/<?cs var:row.id ?>" title="View Suite">
                                    <?cs var:row.title ?>
                                </a>
                            </td>
                            <td class="Component">
                                <?cs var:row.component ?>
                            </td>
                            <td class="description">
                                <?cs var:row.description ?>
                            </td>
                    </tr>
                <?cs /if ?>
            <?cs /each ?>
        </tbody>
    </table>
    <?cs else ?>
        <p class="help">No matches found.</p>
    <?cs /if ?>
    <div class="buttons">
        <form method="post" action="<?cs var:manualtesting.href ?>">
              <input type="submit" name="addsuite" value="Add Test Suite" />
              <input type="hidden" name="manualtesting_action" value="add" />
        </form>
    </div>
    <div class="buttons">
        <form method="post" action="<?cs var:manualtesting.href ?>">
              <input type="submit" name="addsuite" value="Add Test Suite" />
              <input type="hidden" name="manualtesting_action" value="add" />
        </form>
    </div>
</div>

<?cs include "footer.cs" ?>
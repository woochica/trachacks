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
    <h1>{<?cs var:manualtesting.suite.id ?>} <?cs var:manualtesting.suite.title ?></h1>
    <p>
        <?cs var:manualtesting.suite.description ?>
    </p>
    <ul>
        <li><strong>Component: </strong><?cs var:manualtesting.suite.component ?></li>
        <li><strong>Author: </strong><?cs var:manualtesting.suite.user ?></li>
    </ul>
    <p>This is a list of test plans available.</p>
    <?cs if:manualtesting.plans.0.title ?>
    <table class="listing">
        <thead>
            <tr>
                <!--
                columns = ('id','title','description','component','deleted','user')
                -->
                <th><a href="#" title="">Plan</a></th>
                <th><a href="#" title="">Title</a></th>
                <th>Action</td>
            </tr>
        </thead>
        <tbody>
            <?cs set idx = #0 ?>
            <?cs each:row = manualtesting.plans ?>
                <?cs set idx = idx + #1 ?>
                <?cs if:row.title ?>
                    <?cs if idx % #2 ?>
                        <tr class="even">
                    <?cs else ?>
                        <tr class="odd">
                    <?cs /if ?>
                            <td class="plan">
                                <a href="#" title="View Plan">
                                    <?cs var:row.id ?>
                                </a>
                            </td>
                            <td class="title">
                                <a href="#" title="View Plan">
                                    <?cs var:row.title ?>
                                </a>
                            </td>
                            <td>
                                <a href="#">
                                    <img src="/trac/chrome/mt/graphics/pass.png" alt="Pass" />
                                    Pass
                                </a> |
                                <a href="#">
                                    <img src="/trac/chrome/mt/graphics/fail.png" alt="Pass" />
                                    Fail
                                </a>
                            </td>
                        </tr>
                    <?cs if idx % #2 ?>
                        <tr class="even">
                    <?cs else ?>
                        <tr class="odd">
                    <?cs /if ?>
                            <td>
                                <strong>Description</strong>
                            </td>
                            <td colspan="2">
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
        <form action="" method="get">
        <div>
            <input type="submit" value="Create new Test Plan" />
            <input type="hidden" name="action" value="new" />
        </div>
        </form>
    </div>
</div>

<?cs include "footer.cs" ?>
<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>


<div class="mmv_list" id="content" >
    <h1>MMV List</h1>

    <table class="listing" id="milelist">
        <thead>
        <tr><th>Milestone</th>
        </tr>
        </thead>

        <tbody><?cs
        each:item = data ?>
            <tr>
            <td><a href="<?cs var:item.filename ?>" title="<?cs var:item.m_full ?>"><?cs var:item.m_full ?></a></td>
            </tr><?cs
        /each ?>
        </tbody>
    </table>

</div>

<?cs include "footer.cs"?>




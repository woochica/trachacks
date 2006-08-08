<h2>Datamover Configuration</h2>

<form class="mod" id="modconfig" method="post">
    <table class="listing">
        <thead><td>Name</td><td>Path</td><td>&nbsp;</td></thead>
        <tbody>
            <?cs each:env = datamover.envs ?>
            <tr>
                <td><?cs var:env.name ?></td>
                <td><?cs name:env ?></td>
                <td>Button</td>
            </tr>
            <?cs /each ?>
        </tbody>
    </table>
</form>

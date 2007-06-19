<h2>TracForge Prototypes</h2>

<p>
    <!-- <a href="<?cs var:tracforge.href.configset ?>">Config sets</a> -->
</p>
<p>
    <a href="<?cs var:tracforge.href.new ?>">New prototype</a>
</p>

<table class="listing">
<thead>
    <tr>
        <th>Name</th>
        <th></th>
    </tr>
</thead>
<?cs each:tag = tracforge.prototypes.tags ?>
    <tr>
        <td><?cs var:tag ?></td>
        <td><form method="get" action="<?cs var:tracforge.href.prototypes ?>/<?cs var:tag ?>">
                <input type="submit" name="edit" value="Edit" />
        </form></td>
    </tr>
<?cs /each ?>
</table>

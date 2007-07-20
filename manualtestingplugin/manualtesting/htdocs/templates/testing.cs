<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>


<div id="content" class="helloworld">
    <h1>Hello world!</h1>
    <p>This is a test of the public broadcasting system</p>
    <?cs if:data.0.name ?>
        <?cs each:row = data ?>
            <?cs if:row.name ?>
                Name: <?cs var:row.name ?>, Value: <?cs var:row.value ?><br />
            <?cs /if ?>
        <?cs /each ?>
    <?cs else ?>
        <p class="help">There is no data</p>
    <?cs /if ?>
</div>

<?cs include "footer.cs" ?>
<h2>Project Creation Results</h2>

<?cs def:step-text(text) ?>
    <div class="step-text">
    <?cs each:line = text ?>
        <div class="step-line"><?cs var:line ?></div>
    <?cs /each ?>
    </div>
<?cs /def ?>
    

<style type="text/css">
#output, #output tr, #output td {
    margin: 0;
    padding: 0;
}

div.step {
    background-color: #ffd;
    border: 2px groove #000;
    margin: 4px 0;
    padding: 3px 4px;
}

div.step-bad {
    background-color: #f99;
}

.step .step-name {
    font-weight: bold;
    margin-bottom: 5px;
}

.step .step-text {
    background-color: #fff;
    border: 2px groove #000;
    margin-top: 2px;
    margin-bottom: 2px;
    margin-left: 10px;
}

div.line-err {
    background-color: #f99;
    width: 100%;
}

</style>

<table id="output">
<?cs each:step = tracforge.output ?>
<tr><td>
<div class="step step-<?cs if:step.rv ?>good<?cs else ?>bad<?cs /if ?>">
    <span class="step-name"><?cs var:step.action ?></span>
    <span class="step-args">(<?cs var:step.args ?>)</span><br />
    <?cs call:step-text(step.out) ?>
    <?cs call:step-text(step.err) ?>
</div>
</td></tr>
<?cs /each ?>
</table>

<div>
<a href="<?cs var:tracforge.href.projects ?>">Back</a>
</div>

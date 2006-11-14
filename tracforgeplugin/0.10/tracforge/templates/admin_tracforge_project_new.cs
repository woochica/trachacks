<h2>Project Creation Results</h2>

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
<div class="step step-<?cs if:step.2 ?>good<?cs else ?>bad<?cs /if ?>">
    <span class="step-name"><?cs var:step.0 ?></span>
    <span class="step-args">(<?cs var:step.1 ?>)</span><br />
    <div class="step-text">
        <?cs each:text = step.3 ?>
            <div class="line-<?cs var:text.0 ?>"><?cs var:text.1 ?></div>
        <?cs /each ?>
    </div>
</div>
</td></tr>
<?cs /each ?>
</table>

<div>
<a href="<?cs var:tracforge.href.projects ?>">Back</a>
</div>

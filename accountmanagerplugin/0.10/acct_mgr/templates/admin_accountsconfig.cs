<h2>Accounts: Configuration</h2>

<form id="accountsconfig" class="mod" method="post">
<?cs each:section = sections ?>
    <fieldset>
        <legend>
            <label>
                <input type="radio" name="selected" value="<?cs var:section.classname ?>" 
                       <?cs if:section.selected ?>checked="checked"<?cs /if ?> />
                <?cs var:section.name ?>
            </label>
        </legend>
        
        <?cs each:option = section.options ?>
            <div class="field">
                <label><?cs var:option.label ?>:
                    <input type="text" name="<?cs var:option.name ?>" value="<?cs var:option.value ?>"
                           class="textwidget" />
                </label>
            </div>
        <?cs /each ?>
    </fieldset>
<?cs /each ?>
<div class="buttons">
    <input type="submit" name="save" value="Save" />
</div>
</form>

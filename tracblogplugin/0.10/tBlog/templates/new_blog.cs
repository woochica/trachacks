<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
    <h2>Wiki Navigation</h2>
    <ul>
        <li><a href="<?cs var:trac.href.wiki ?>">Start Page</a></li>
        <li><a href="<?cs var:trac.href.wiki ?>/TitleIndex">Title Index</a></li>
        <li><a 
            href="<?cs var:trac.href.wiki ?>/RecentChanges">Recent Changes</a>
            </li>
    </ul>
    <hr />
</div>

<div id="content" class="wiki">
    <h1>Create Blog Entry</h1>
    <?cs if blog.action == "preview" ?>
        <fieldset id="preview">
            <legend>Preview (<a href="#edit">skip</a>)</legend>
            <div class="wikipage"><?cs var:blog.page_html ?></div>
        </fieldset>
    <?cs /if ?>
    <form id="edit" method="post">
        <input type="hidden" name="referer" value="<?cs var:blog.referer ?>" />
        <fieldset class="iefix">
            <input type="hidden" name="action" value="edit" />
            <input type="hidden" id="scroll_bar_pos" name="scroll_bar_pos" 
            value="<?cs var:wiki.scroll_bar_pos ?>" />
            <div class="field">
                <label>Entry Title<br />
                    <input id="comment" type="text" name="blogtitle" size="60" 
                    value="<?cs var:blog.title?>" />
                </label>
            </div><br />
            <div id="rows">
                <label for="editrows">Adjust edit area height:</label>
                <select size="1" name="editrows" id="editrows" tabindex="43"
                onchange="resizeTextArea('text', this.options[selectedIndex].value)">
                    <?cs loop:rows = 8, 42, 4 ?>
                        <option value="<?cs var:rows ?>"
                            <?cs if:rows == blog.edit_rows ?> 
                                selected="selected"<?cs /if ?>>
                            <?cs var:rows ?>
                        </option>
                    <?cs /loop ?>
                </select>
            </div>
            <p>
                <textarea id="text" class="wikitext" name="text" cols="80" 
                rows="<?cs var:blog.edit_rows ?>"><?cs var:blog.page_source ?></textarea>
            </p>
            <script type="text/javascript">
                var scrollBarPos = document.getElementById("scroll_bar_pos");
                var text = document.getElementById("text");
                (window, "load", function() {
                    if (scrollBarPos.value) text.scrollTop = scrollBarPos.value;
                });
                addEvent(text, "blur", function() { 
                    scrollBarPos.value = text.scrollTop
                });
            </script>
        </fieldset>
        <div id="help">
            <b>Note:</b> See <a 
            href="<?cs var:$trac.href.wiki ?>/WikiFormatting">WikiFormatting</a>
            and <a href="<?cs var:$trac.href.wiki ?>/TracWiki">TracWiki</a> for
            help on editing wiki content.
        </div>
        <fieldset id="changeinfo">
            <legend>Change information</legend>
<!--
            <div class="field">
                <label>Your email or username:<br />
                    <input id="author" type="text" name="author" size="30" 
                    value="<?cs var:blog.author ?>" />
                </label>
            </div>
-->
            <div class="field">
                <label for="tags">Tag under: (<a 
                href="<?cs var:base_url ?>/tags">view all tags</a>)</label>
                <br/>
                <input title="Comma separated list of tags" type="text" 
                id='tags' name="tags" size="30" value="<?cs var:tags ?>">
            </div>

            <div class="field">
                <label>Wiki Page name:<br />
                    <input id="pagename" type="text" name="pagename" size="60" 
                    value="<?cs var:blog.pagename?>" />
                </label>
            </div><br />
            <?cs if trac.acl.WIKI_ADMIN ?>
                <div class="options">
                    <label>
                        <input type="checkbox" name="readonly" id="readonly"
                        <?cs if blog.readonly == "1"?>
                            checked="checked"
                        <?cs /if ?> />
                        Page is read-only
                    </label>
                </div>
            <?cs /if ?>
        </fieldset>
        <div class="buttons">
            <?cs if blog.action == "collision" ?>
                <input type="submit" name="preview" value="Preview" 
                disabled="disabled" />&nbsp;
                <input type="submit" name="save" value="Submit changes" 
                disabled="disabled" />&nbsp;
            <?cs else ?>
                <input type="submit" name="preview" value="Preview" 
                accesskey="r" />&nbsp;
                <input type="submit" name="save" value="Submit changes" />&nbsp;
            <?cs /if ?>
            <input type="submit" name="cancel" value="Cancel" />
        </div>
        <script type="text/javascript" 
            src="<?cs var:htdocs_location ?>js/wikitoolbar.js">
        </script>
    </form>
</div>

<?cs include "footer.cs" ?>

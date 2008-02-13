<h2>Blog Admin<?cs if blogadmin.page == 'defaults' ?> -- Defaults<?cs /if ?></h2>

<?cs if blogadmin.page == 'defaults' ?>
    <form class="mod" id="modbasic" method="post">
        <fieldset>
            <legend>Defaults</legend>
            <div class="blogoptions">
            <div class="field">
                <label>Date Format String:<br />
                    <input type="text" name="date_format" 
                    value="<?cs var:blogadmin.date_format ?>" />
                </label>
            </div>
            <div class="field">
                <label>Page Name Format String:<br />
                    <input type="text" name="page_format" 
                    value="<?cs var:blogadmin.page_format ?>" />
                </label>
            </div>
            <div class="field">
                <label>Default Tag (<a href="<?cs var:base_url ?>/tags"
                    >view all tags</a>):<br/>
                    <input type="text" name="default_tag" 
                    value="<?cs var:blogadmin.default_tag ?>" />
                </label>
            </div>
            <div class="field">
                <label>Post Max Size:<br/>
                    <input type="text" name="post_size" 
                    value="<?cs var:blogadmin.post_size ?>" />
                </label>
            </div>
            <div class="field">
                <label>Days of History:<br/>
                    <input type="text" name="history_days" 
                    value="<?cs var:blogadmin.history_days ?>" />
                </label>
            </div>
            <div class="field">
                <label>Number of Posts:<br/>
                    <input type="text" name="num_posts" 
                    value="<?cs var:blogadmin.num_posts ?>" />
                </label>
            </div>
            <div class="field">
                <label>New Blog Link:<br/>
                    <input type="text" name="new_blog_link" 
                    value="<?cs var:blogadmin.new_blog_link ?>" />
                </label>
            </div>
            <div class="field">
                <label>Calendar Week Start Day:<br/>
                    <input type="text" name="first_week_day" 
                    value="<?cs var:blogadmin.first_week_day ?>" />
                </label>
            </div>
            <div class="field">
                <label>Mark Updated Posts:<br/>
                    <input type="text" name="mark_updated" 
                    value="<?cs var:blogadmin.mark_updated ?>" />
                </label>
            </div>
            <div class="field">
                <label>Show Link in Nav Bar:<br/>
                    <input type="text" name="nav_bar" 
                    value="<?cs var:blogadmin.nav_bar ?>" />
                </label>
            </div>
            <div class="field">
                <label>Macro Blacklist:<br/>
                    <input type="text" name="macro_blacklist" 
                    value="<?cs var:blogadmin.macro_blacklist ?>" />
                </label>
            </div>
            <div class="field">
                <label>Footer:<br/>
                    <textarea name="footer" cols=30 rows=6><?cs var:blogadmin.footer ?></textarea>
                </label>
            </div>
        <div class="buttons">
            <input type="submit" value="Apply Changes" />
        </div>
            </div>
            <div class="blogdocs">
                <div id="content" class="wiki">
                    <div class="wikipage">
                        <fieldset>
                            <legend>Docs</legend>
                            <?cs var:blogadmin.docs ?>
                        </fieldset>
                    </div>
                </div>
            </div>
        </fieldset>
    </form>
<?cs /if ?>

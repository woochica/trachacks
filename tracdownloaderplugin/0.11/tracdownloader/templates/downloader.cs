<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include:"downloads_cntx_nav.cs" ?>
<div id="content">

<h1>Downloader</h1>

<?cs if:download_link ?>
<form action="" class="addnew">
    <p><br/></p>
    <fieldset>
        <legend><?cs var:download_name ?></legend>
        
        <h3><a href="<?cs var:download_link ?>">Download!</a></h3>
        <p>Download your file <a href="<?cs var:download_link ?>"><?cs var:download_name ?></a> 
        by clicking one of these links.</p><p><?cs if:form_only_first_time 
        ?>Now you can download any file directly without filling form again...<?cs /if ?></p>
    </fieldset>
</form>
<?cs /if ?>

<?cs if:subcount(quest) ?>
<form id="quest" class="addnew" action="" method="post" enctype="multipart/form-data">
    <div><br/></div>
    <fieldset>
          <legend>Download form:</legend>
          <p>You must correctly fill this form before you can download any file.</p>
          <?cs if:subcount(quest.errors) ?>
          <p>
            <strong class="err">Invalidity detected:</strong>
            <ul>
            <?cs each:err = quest.errors ?>
                <?cs if:err ?>
                    <li><span class="err"><?cs var:err ?></span><br/></li>
                <?cs /if ?>
            <?cs /each ?>
            </ul>
          </p>
          <?cs /if ?>
          
          <?cs each:q = quest ?>
            <?cs if:q.label_for && !q.cat ?>
              <?cs set:q.cat=q.label_for ?>
            <?cs /if ?>
            <?cs if:now_in_category!=q.cat ?>
                <?cs set:now_in_category=q.cat ?>
                <br/>
            <?cs /if ?>
            <?cs if q.type == 'text' ?>
                <div class="field">
                  <label><?cs var:q.label?><br/><input type="text" name="<?cs var:q.name?>" 
                  value="<?cs var:q.value?>"/><?cs if:q.bad 
                    ?><span class="err"> *</span><?cs 
                  /if ?></label>
                </div>
            <?cs /if ?>
            <?cs if q.type == 'radio' ?>
                <div class="field">
                  <label><input type="radio" name="<?cs var:q.name?>" 
                  value="<?cs var:q.value?>" <?cs 
                    if q.selected ?>checked="checked"<?cs /if 
                    ?> /><?cs var:q.label?><?cs if:q.bad 
                    ?><span class="err"> *</span><?cs 
                  /if ?></label>
                </div>
            <?cs /if ?>
            <?cs if q.type == 'checkb' ?>
                <div class="field">
                  <label><input type="checkbox" name="<?cs var:q.name?>" 
                  value="<?cs var:q.value?>" <?cs 
                    if q.selected ?>checked="checked"<?cs /if 
                    ?> /><?cs var:q.label?><?cs if:q.bad 
                    ?><span class="err"> *</span><?cs 
                  /if ?></label>
                </div>
            <?cs /if ?>
            <?cs if q.type == 'label' ?>
                <div class="field">
                  <strong><?cs var:q.text?></strong>
                </div>
            <?cs /if ?>
            
          <?cs /each ?>
          
          <?cs if:quest.captcha_id ?>
                <br/>
                <input type="hidden" name="captcha_key" value="<?cs var:quest.captcha_id ?>" />
                <div class="field">
                  <img class="cap_img" src="<?cs var:quest.captcha_adr ?>" alt="Captcha image" />
                  <label>Code from picture:<input type="text" name="captcha" value="" />
                  <?cs if:captcha_bad 
                    ?><span class="err"> *</span><?cs /if 
                  ?></label>
                </div>
          <?cs /if ?>
          
          <div class="buttons">
            <input type="submit" name="submit" value="Download file!" />
          </div>
    </fieldset>
</form>
<?cs /if ?>

<?cs if notes ?>
    <h2>Release notes of <?cs var:notes.for ?></h2>
    
    <div class="relnotes">
        <?cs each:line = notes.text ?>
            <code><?cs var:line ?></code><br/>
        <?cs /each ?>
    </div>
<hr class="tiny" />
<h2>Files for download:</h2>
<?cs /if ?>


<?cs include:"downloads_list.cs" ?>

</div>
<?cs include "footer.cs"?>

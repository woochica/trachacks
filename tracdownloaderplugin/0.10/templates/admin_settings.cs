<?cs include:"downloads_cntx_nav.cs" ?>

<?cs def:file_directory_form() ?>
     <fieldset>
        <legend>Files directory</legend>
        <div class="field">
      <label>Directory to store files:<br />
       <input type="text" id="files_dir" name="files_dir" value="<?cs
         var:files_dir ?>" size="70"/>
      </label>
      <p class="help1">This is the most important thing to set-up, without accesable file directory will no part od Downloader plug-in work. You should set this full system path to place which is not readable by web server to avoid downloading files without policy defined in Downloader. Good path for files is for example "<code>your_trac_project_dir/downloader</code>". Make sure that directory is readable by user under which is the Python interpreter running. When you already have any file uploaded to Downloader, you must copy files from original directory to new one before changing this path, in other way downloader will not work correctly.</p>
     </div>
     </fieldset>
<?cs /def ?>

<h2>Downloader settings</h2>

<form class="mod" id="modlog" method="post">

<?cs if:file_dir_not_set ?><h3 class="err">Files directory is not set or unaccesable!</h3><p class="help1 err">Make sure that files directory you set is readable for python or set another. You should submit this TWO TIMES to changes take effect.</p>
<?cs call:file_directory_form() ?>
<?cs /if ?>

<fieldset>
 <legend>Downloading</legend>
 <div class="field">
  <label>
     <input type="checkbox" name="no_quest" value="<?cs var:no_quest ?>" <?cs 
        if:no_quest == 1?> checked="checked"<?cs /if ?>/>
     don't use Questionnaire
  </label>
  <p class="help1">If checked, there will be no questionnaire on download page, so no information about downloads and no stats availible.</p>
 </div>
 <div class="field">
  <label>
     <input type="checkbox" name="form_only_first_time" value="<?cs var:form_only_first_time ?>" <?cs 
        if:form_only_first_time == 1?> checked="checked"<?cs /if ?>/>
     show questionnaire only for first download in users session
  </label>
  <p class="help1">If checked, questionnaire will be shown only for the first download in user's session, data for all downloads in session will be filled same.</p>
 </div>
 <div class="field">
  <label>
     <input type="checkbox" name="provide_link" value="<?cs var:form_only_first_time ?>" <?cs 
        if:provide_link == 1?> checked="checked"<?cs /if ?>/>
     provide link for download
  </label>
  <p class="help1">If checked then after correct filling of questionnaire will be prvided link for requested file. If unchecked, user will be redirected to file right after sending correct questionnaire so files with MIME types known for his browser (like .txt, .pdf, .doc) will be directly displayed.</p>
 </div>
</fieldset>
<br/>
<fieldset>
 <legend>Captcha</legend>
  <div class="field">
  <?cs if:!cap_work ?><p class="err"><strong>Captcha is currently unavailible</strong>, because Downloader was unable to include Captcha module. If you like to use PyCaptcha, check if captcha directory is installed and in module path or mentioned in file <code>python_dir/lib/site-packages/easy-install.pth</code>. Problem colud be absence of PIL (Python Imaging Library) too.<br/></p><?cs /if ?>
  <label>
     <input type="checkbox" name="no_captcha" value="<?cs var:no_captcha ?>" <?cs 
        if:no_captcha == 1?> checked="checked"<?cs /if ?><?cs if:!cap_work ?> disabled="disabled"<?cs /if ?>/>
     don't use Captcha
  </label>
  <p class="help1">Captcha is picture with text in the form used to distinguish robosts and humans. For using Captcha you need to have PyCaptcha ver. >= 0.4 and PIL (Python Imaging Library) >= 1.1.5  installed.</p>
 </div>
 <div class="field">
  <label>Number of letters:<br />
   <input type="text" id="captcha_num_of_letters" name="captcha_num_of_letters" value="<?cs
     var:captcha_num_of_letters ?>" <?cs if:!cap_work ?> disabled="disabled"<?cs /if ?>/>
  </label>
  <p class="help1">Number of letters in Captcha picture. Be caruful, with more letters you must set appropirate size of font (the best is refreshing form witch Captcha several times to see if all letters are visible).</p>
 </div>
 <div class="field">
  <label>Font size:<br />
   <input type="text" id="captcha_font_size" name="captcha_font_size" value="<?cs
     var:captcha_font_size ?>" <?cs if:!cap_work ?> disabled="disabled"<?cs /if ?>/>
  </label>
 </div>
 <div class="field">
  <label>Font border:<br />
   <input type="text" id="captcha_font_border" name="captcha_font_border" value="<?cs
     var:captcha_font_border ?>" <?cs if:!cap_work ?> disabled="disabled"<?cs /if ?>/>
  </label>
 </div>
  <div class="field">
  <label>Hardness:<br />
   <select id="captcha_hardness" name="captcha_hardness" <?cs if:!cap_work ?> disabled="disabled"<?cs /if ?>><?cs
    each:hardness = captcha_hardness_list ?><option value="<?cs var:hardness ?>"<?cs
     if:hardness==captcha_hardness ?> selected="selected"<?cs /if ?>><?cs
     var:hardness ?></option><?cs
    /each ?></select>
  </label>
 </div>
 </fieldset>
 <br/>
 <?cs if:!file_dir_not_set ?><?cs call:file_directory_form() ?><?cs /if ?>
 
 <div class="field">
 <div class="buttons">
  <input type="submit" value="Apply changes">
 </div>
 <p class="help1">You may need to restart the server for these changes to take
 effect.</p>
</form>

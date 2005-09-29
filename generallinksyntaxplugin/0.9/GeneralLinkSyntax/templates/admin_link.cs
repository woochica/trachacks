<h2>Manage Links</h2><?cs
if:admin.message.text ?>
 <span class='<?cs var:admin.message.class ?>' ><?cs
 var:admin.message.text ?></span><br/><?cs
/if ?>
<?cs def:helptext() ?>
 <p class='help'>
 'Expose' means to tell trac it is used as wiki link.
 If you want to expose, containing separator character is not
 good because trac could not find as namespace (without patch).</p>
 <p class='help'>
 'Display' is a optional display text of link anchor. 
 'URL' is target location for this link.
 'Display' and 'URL' can be contain one '%s'
 to replace with an argument. If 'Display' is omitted,
 "<i>name</i>" or "<i>name</i>:<i>arg</i>" is used.
 </p>
<?cs /def ?><?cs
if:admin.link.mode == 'modify' ?>
 <form id='modlink' class='mod' method='post'>
  <fieldset>
   <legend>Edit Link : <?cs var:admin.link.name ?></legend>
   <div class='field'>
    <label><input name='expose' type='checkbox'<?cs
    if admin.link.expose ?>checked='checked'<?cs /if ?> />
	Expose</label>
   </div>
   <div class='field'>
    <label>Display: <input name='disp' class='disp' type='text'
    value='<?cs var:admin.link.disp ?>' /> (optional)</label>
   </div>
   <div class='field'>
    <label>URL: <input name='url' class='url' type='text'
    value='<?cs var:admin.link.url ?>' /></label>
   </div>
   <div class='buttons'>
    <input type='submit' name='cancel' value='Cancel' />
    <input type='submit' name='save'   value='Save' />
   </div>
   <div style='color: #666; font-size: 90%; margin: 1em 0 .5em'>
    <p class='help'>Edit link definition.</p>
    <?cs call:helptext() ?>
   </div>
  </fieldset>
</form><?cs

else ?>
 <form id='addlink' class='addnew' method='post'>
  <fieldset>
   <legend>New link</legend>
   <div class='field'>
    <label>Name:<br/><input name='name' class='name' type='text'
/></label>
    <br/>
    <label><input name='expose' type='checkbox'<?cs
    if admin.link.expose ?>checked='checked'<?cs /if ?> />
	Expose</label>
   </div>
   <div>
    <label>Display: <br/><input name='disp' class='disp' type='text' /></label>
   </div>
   <div class='field'>
    <label>URL: <br/><input name='url' class='url' type='text' /></label>
   </div>
   <div class='buttons'>
    <input type='submit' name='add' id='add' value='Add' />
   </div>
   <div>
    <p class='help'>Add new link entry.</p>
    <p class='help'>
    'Name' should be consist with alphabets and numbers which can be
    joind with single separator ('-', '+' or '_') character.</p>
    <?cs call:helptext() ?>
   </div>
  </fieldset>
 </form>

 <form method='post'>
  <p class='help'>Link is a alias of URL. You can use it in wiki
  enabled area like "<tt>link:<i>name</i></tt>".
  It will be rendered as anchor to defined 'URL' with 'Display' text.
  Link can be take one argument like "<tt>link:<i>name</i>:<i>arg</i></tt>"
  and 'URL' and 'Display' can contain "<tt>%s</tt>" for the place of
  argument replacement.
  If you set as exposed, <i>name</i> will be exposed as wiki synax.
  Then you can use like "<i>name</i>:<i>arg</i>" without
  "<tt>link:</tt>" prefix.
  </p>
  <table class='listing' id='linklist'>
   <thead>
    <tr>
     <th class='sel'>&nbsp;</th>
     <th>Name</th>
     <th>Display</th>
    </tr>
   </thead><tbody><?cs
	each:link = admin.links ?><tr>
	  <td class='sel'><input type='checkbox' name='sel'
		   value='<?cs var:link.name ?>'/></td>
	  <td class='name'><a href='<?cs var:link.href ?>'><?cs
	    var:link.name ?></a><?cs
	    if:link.expose ?> (exposed)<?cs /if ?></td>
	  <td class='disp'><?cs var:link.disp ?></td>
          <!--
          </tr><tr><td class='url' colspan=2 style='overflow:hidden'><?cs var:link.url ?></td>
          -->
	 </tr><?cs
	/each ?>
   </tbody>
  </table>
  <div class='buttons'>
   <input type='submit' name='remove' value='Remove selected'>
  </div>
 </form><?cs
/if ?>

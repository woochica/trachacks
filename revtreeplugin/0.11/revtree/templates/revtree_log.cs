<div id="revtree">
  <dl id="overview"><?cs
   if:changeset.chgset ?>
   <dt class="property time">Timestamp:</dt>
   <dd class="time"><?cs var:changeset.time ?> 
    (<?cs alt:changeset.age ?>less than one hour<?cs /alt ?> ago)</dd>
   <dt class="property author">Author:</dt>
   <dd class="author"><?cs var:changeset.author ?></dd>
   <dt class="property message">Message:</dt>
   <dd class="message"><?cs
    alt:changeset.message ?>&nbsp;<?cs /alt ?></dd><?cs
   /if ?>
  </dl>
</div>

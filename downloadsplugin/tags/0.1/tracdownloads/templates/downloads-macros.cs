<?cs def:sortable_th(order, desc, class, title, href) ?>
  <th class="<?cs var:class ?><?cs if:order == class ?> <?cs if:desc ?>desc<?cs else ?>asc<?cs /if ?><?cs /if ?>">
    <a title="Sort by <?cs var:class ?><?cs if:order == class && !desc ?> (descending)<?cs /if ?>" href="<?cs var:href ?>?order=<?cs var:class ?><?cs if:order == class && !desc ?>&amp;desc=1<?cs /if ?>">
      <?cs var:title ?>
    </a>
  </th>
<?cs /def ?>
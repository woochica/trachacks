<table class="visitcounter">
  <tr>
    <?cs if:visitcounter.show_digits ?>
      <?cs each:digit = visitcounter.digits ?><td class="digit digit<?cs var:digit ?>"></td><?cs /each ?>
    <?cs else ?>
      <td><?cs var:visitcounter.count ?></td>
    <?cs /if ?>
  </tr>
</table>
<data>
    <?cs each:e = timeline.events ?>
    <event start="<?cs var:e.date ?> <?cs var:e.time ?>" title="<?cs var:html_escape(e.title) ?>" link="<?cs var:e.href ?>" icon="<?cs var:e.icon ?>"><?cs var:e.message?></event>
    <?cs /each ?>
</data>

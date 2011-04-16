{   'headers': [   {'col': 'ticket', 'title': 'ticket'},
                   {'col': 'summary', 'title': 'Summary'},
                   {'col': 'owner', 'title': 'Owner'},
                   {'col': 'priority', 'title': 'Priority'},
                   {'col': 'component', 'title': 'Component'},
                   {'col': 'mycustomfield', 'title': 'Mycustomfield'},
                   {'col': 'comment', 'title': 'Comment'}],
    'message': Markup(u"""\
<style type="text/css">
.ticket-imported, .modified-ticket-imported { width: 40px; }
.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-summary, .modified-owner, .modified-priority, .modified-component, .modified-mycustomfield, .modified-comment { font-style: italic; }
</style>
<p>
Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.
</p>
<ul><li>3 tickets will be imported (1 added, 1 modified, 1 unchanged).
</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.
</li><li>Some Trac fields are not present in the import. They will default to:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>Default value</strong>
</td></tr><tr><td>Description, Cc, Milestone, Version, Keywords, Severity</td><td><em>(Empty value)</em>
</td></tr><tr><td>Status</td><td>new
</td></tr><tr><td>Changetime</td><td><em>(now)</em>
</td></tr><tr><td>Reporter</td><td>testuser
</td></tr><tr><td>Resolution</td><td><em>(None)</em>
</td></tr><tr><td>Time</td><td><em>(now)</em>
</td></tr><tr><td>Type</td><td>task
</td></tr></table>
</blockquote>
</blockquote>
<p>
(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).
</p>
<ul><li>Some fields will not be imported because they don\'t exist in Trac: anyotherfield.
</li><li>The field "comment" will be used as comment when modifying tickets, and appended to the description for new tickets.
</li><li>Some lookup values are not found and will be added to the possible list of values:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>New values</strong>
</td></tr><tr><td>Component</td><td>again again mycomp again
</td></tr></table>
</blockquote>
</blockquote>
<ul><li>Some user names do not exist in the system: me again modified. Make sure that they are valid users.
</li></ul><br/>"""),
    'rows': [   {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': 1246},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'sum1'},
                                 {   'col': 'owner',
                                     'style': 'modified-owner',
                                     'value': u'me again modified'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'mypriority'},
                                 {   'col': 'component',
                                     'style': 'modified-component',
                                     'value': u'again again mycomp again'},
                                 {   'col': 'mycustomfield',
                                     'style': 'modified-mycustomfield',
                                     'value': u'mycustomfield1 modified'},
                                 {   'col': 'comment',
                                     'style': 'comment',
                                     'value': u'comment with some modified fields'}],
                    'style': ''},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': 1245},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'sum2'},
                                 {   'col': 'owner',
                                     'style': 'owner',
                                     'value': u'you'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'yourpriority'},
                                 {   'col': 'component',
                                     'style': 'component',
                                     'value': u'yourcomp'},
                                 {   'col': 'mycustomfield',
                                     'style': 'mycustomfield',
                                     'value': u'customfield2'},
                                 {   'col': 'comment',
                                     'style': 'comment',
                                     'value': u'comment with no field modified'}],
                    'style': ''},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'newticket'},
                                 {   'col': 'owner',
                                     'style': 'owner',
                                     'value': u'you'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'yourpriority'},
                                 {   'col': 'component',
                                     'style': 'component',
                                     'value': u'yourcomp'},
                                 {   'col': 'mycustomfield',
                                     'style': 'mycustomfield',
                                     'value': u'customfield2'},
                                 {   'col': 'comment',
                                     'style': 'comment',
                                     'value': u' comment for a new ticket'}],
                    'style': 'color-new-even'}],
    'title': 'Preview Import'}

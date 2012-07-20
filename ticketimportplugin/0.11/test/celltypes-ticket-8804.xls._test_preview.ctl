{   u'headers': [   {   u'col': u'ticket', u'title': u'ticket'},
                    {   u'col': u'summary', u'title': u'Summary'},
                    {   u'col': u'owner', u'title': u'Owner'},
                    {   u'col': u'type', u'title': u'Type'},
                    {   u'col': u'status', u'title': u'Status'},
                    {   u'col': u'priority', u'title': u'Priority'}],
    u'message': Markup(u"""\
<style type="text/css">
.ticket-imported, .modified-ticket-imported { width: 40px; }
.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-summary, .modified-owner, .modified-type, .modified-status, .modified-priority { font-style: italic; }
</style>
<p>
Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.
</p>
<ul><li>6 tickets will be imported (6 added, 0 modified, 0 unchanged).
</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.
</li><li>Some Trac fields are not present in the import. They will default to:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>Default value</strong>
</td></tr><tr><td>Description, Cc, Milestone, Component, Version, Keywords, Severity</td><td><i>(Empty value)</i>
</td></tr><tr><td>Changetime</td><td><i>(now)</i>
</td></tr><tr><td>Reporter</td><td>testuser
</td></tr><tr><td>Resolution</td><td><i>(None)</i>
</td></tr><tr><td>Time</td><td><i>(now)</i>
</td></tr></table>
</blockquote>
</blockquote>
<p>
(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).
</p>
<ul><li>A value for the "Status" field does not exist: open. It will be imported, but will result in an invalid status.
</li></ul><ul><li>Some lookup values are not found and will be added to the possible list of values:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>New values</strong>
</td></tr><tr><td>Priority</td><td>String, 1234, 2011-05-18 01:37, TRUE, #N/A
</td></tr></table>
</blockquote>
</blockquote>
<ul><li>Some user names do not exist in the system: jun66j5. Make sure that they are valid users.
</li></ul><br/>"""),
    u'rows': [   {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'XL_CELL_EMPTY'},
                                   {   u'col': u'owner',
                                       u'style': u'owner',
                                       u'value': u'jun66j5'},
                                   {   u'col': u'type',
                                       u'style': u'type',
                                       u'value': u'task'},
                                   {   u'col': u'status',
                                       u'style': u'status',
                                       u'value': u'open'},
                                   {   u'col': u'priority',
                                       u'style': u'priority',
                                       u'value': u''}],
                     u'style': u'color-new-even'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'XL_CELL_TEXT'},
                                   {   u'col': u'owner',
                                       u'style': u'owner',
                                       u'value': u'jun66j5'},
                                   {   u'col': u'type',
                                       u'style': u'type',
                                       u'value': u'task'},
                                   {   u'col': u'status',
                                       u'style': u'status',
                                       u'value': u'open'},
                                   {   u'col': u'priority',
                                       u'style': u'priority',
                                       u'value': u'String'}],
                     u'style': u'color-new-odd'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'XL_CELL_NUMBER'},
                                   {   u'col': u'owner',
                                       u'style': u'owner',
                                       u'value': u'jun66j5'},
                                   {   u'col': u'type',
                                       u'style': u'type',
                                       u'value': u'task'},
                                   {   u'col': u'status',
                                       u'style': u'status',
                                       u'value': u'open'},
                                   {   u'col': u'priority',
                                       u'style': u'priority',
                                       u'value': u'1234'}],
                     u'style': u'color-new-even'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'XL_CELL_DATE'},
                                   {   u'col': u'owner',
                                       u'style': u'owner',
                                       u'value': u'jun66j5'},
                                   {   u'col': u'type',
                                       u'style': u'type',
                                       u'value': u'task'},
                                   {   u'col': u'status',
                                       u'style': u'status',
                                       u'value': u'open'},
                                   {   u'col': u'priority',
                                       u'style': u'priority',
                                       u'value': u'2011-05-18 01:37'}],
                     u'style': u'color-new-odd'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'XL_CELL_BOOLEAN'},
                                   {   u'col': u'owner',
                                       u'style': u'owner',
                                       u'value': u'jun66j5'},
                                   {   u'col': u'type',
                                       u'style': u'type',
                                       u'value': u'task'},
                                   {   u'col': u'status',
                                       u'style': u'status',
                                       u'value': u'open'},
                                   {   u'col': u'priority',
                                       u'style': u'priority',
                                       u'value': u'TRUE'}],
                     u'style': u'color-new-even'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'XL_CELL_ERROR'},
                                   {   u'col': u'owner',
                                       u'style': u'owner',
                                       u'value': u'jun66j5'},
                                   {   u'col': u'type',
                                       u'style': u'type',
                                       u'value': u'task'},
                                   {   u'col': u'status',
                                       u'style': u'status',
                                       u'value': u'open'},
                                   {   u'col': u'priority',
                                       u'style': u'priority',
                                       u'value': u'#N/A'}],
                     u'style': u'color-new-odd'}],
    u'title': u'Preview Import'}

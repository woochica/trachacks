{   u'headers': [   {   u'col': u'ticket', u'title': u'ticket'},
                    {   u'col': u'summary', u'title': u'Summary'}],
    u'message': Markup(u"""\
<style type="text/css">
.ticket-imported, .modified-ticket-imported { width: 40px; }
.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-summary { font-style: italic; }
</style>
<p>
Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.
</p>
<ul><li>5 tickets will be imported (5 added, 0 modified, 0 unchanged).
</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.
</li><li>Some Trac fields are not present in the import. They will default to:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>Default value</strong>
</td></tr><tr><td>Description, Cc, Milestone, Component, Version, Mycustomfield, Keywords, Severity</td><td><i>(Empty value)</i>
</td></tr><tr><td>Status</td><td>new
</td></tr><tr><td>Changetime</td><td><i>(now)</i>
</td></tr><tr><td>Reporter</td><td>testuser
</td></tr><tr><td>Resolution</td><td><i>(None)</i>
</td></tr><tr><td>Priority</td><td>major
</td></tr><tr><td>Time</td><td><i>(now)</i>
</td></tr><tr><td>Type</td><td>task
</td></tr></table>
</blockquote>
</blockquote>
<p>
(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).
</p>
<ul><li>Some fields will not be imported because they don\'t exist in Trac: #blockedby, #wbs.
</li></ul><br/>"""),
    u'rows': [   {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'Design schematic'}],
                     u'style': u'color-new-even'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'Layout board'}],
                     u'style': u'color-new-odd'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'Check board'}],
                     u'style': u'color-new-even'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'Manufacture prototypes'}],
                     u'style': u'color-new-odd'},
                 {   u'cells': [   {   u'col': u'ticket',
                                       u'style': u'',
                                       u'value': u'(new)'},
                                   {   u'col': u'summary',
                                       u'style': u'summary',
                                       u'value': u'Verify prototypes'}],
                     u'style': u'color-new-even'}],
    u'title': u'Preview Import'}
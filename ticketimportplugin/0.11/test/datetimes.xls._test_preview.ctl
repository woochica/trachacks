{   'headers': [   {'col': 'ticket', 'title': 'ticket'},
                   {'col': 'Summary', 'title': 'Summary'},
                   {'col': 'MyDate', 'title': 'Mydate'},
                   {'col': 'MyDateTime', 'title': 'Mydatetime'}],
    'message': Markup(u"""\
<style type="text/css">
.ticket-imported, .modified-ticket-imported { width: 40px; }
.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-Summary, .modified-MyDate, .modified-MyDateTime { font-style: italic; }
</style>
<p>
Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.
</p>
<ul><li>2 tickets will be imported (2 added, 0 modified, 0 unchanged).
</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.
</li><li>Some Trac fields are not present in the import. They will default to:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>Default value</strong>
</td></tr><tr><td>Description, Cc, Milestone, Component, Version, Keywords, Severity</td><td><i>(Empty value)</i>
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
<br/>"""),
    'rows': [   {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'Summary',
                                     'style': 'Summary',
                                     'value': u'summary1'},
                                 {   'col': 'MyDate',
                                     'style': 'MyDate',
                                     'value': '01/01/10'},
                                 {   'col': 'MyDateTime',
                                     'style': 'MyDateTime',
                                     'value': '01/01/10'}],
                    'style': 'color-new-even'},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'Summary',
                                     'style': 'Summary',
                                     'value': u'summary2'},
                                 {   'col': 'MyDate',
                                     'style': 'MyDate',
                                     'value': '12/23/65'},
                                 {   'col': 'MyDateTime',
                                     'style': 'MyDateTime',
                                     'value': '12/23/71'}],
                    'style': 'color-new-odd'}],
    'title': 'Preview Import'}

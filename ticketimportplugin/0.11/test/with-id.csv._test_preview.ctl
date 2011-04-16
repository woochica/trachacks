{   'headers': [   {'col': 'ticket', 'title': 'ticket'},
                   {'col': 'owner', 'title': 'Owner'},
                   {'col': 'priority', 'title': 'Priority'},
                   {'col': 'component', 'title': 'Component'},
                   {'col': 'mycustomfield', 'title': 'Mycustomfield'}],
    'message': Markup(u"""\
<style type="text/css">
.ticket-imported, .modified-ticket-imported { width: 40px; }
.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-owner, .modified-priority, .modified-component, .modified-mycustomfield { font-style: italic; }
</style>
<p>
Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.
</p>
<ul><li>3 tickets will be imported (1 added, 2 modified, 0 unchanged).
</li><li>A <strong>ticket</strong> column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.
</li><li>Some Trac fields are not present in the import. They will default to:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>Default value</strong>
</td></tr><tr><td>Description, Cc, Milestone, Version, Keywords, Severity</td><td><i>(Empty value)</i>
</td></tr><tr><td>Status</td><td>new
</td></tr><tr><td>Changetime</td><td><i>(now)</i>
</td></tr><tr><td>Reporter</td><td>testuser
</td></tr><tr><td>Resolution</td><td><i>(None)</i>
</td></tr><tr><td>Time</td><td><i>(now)</i>
</td></tr><tr><td>Type</td><td>task
</td></tr></table>
</blockquote>
</blockquote>
<p>
(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).
</p>
<ul><li>Some fields will not be imported because they don\'t exist in Trac: anyotherfield.
</li><li>Some lookup values are not found and will be added to the possible list of values:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>New values</strong>
</td></tr><tr><td>Priority</td><td>herpriority
</td></tr><tr><td>Component</td><td>hercomp
</td></tr></table>
</blockquote>
</blockquote>
<ul><li>Some user names do not exist in the system: me, you, she. Make sure that they are valid users.
</li></ul><br/>"""),
    'rows': [   {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': u'1'},
                                 {   'col': 'owner',
                                     'style': 'modified-owner',
                                     'value': u'me'},
                                 {   'col': 'priority',
                                     'style': 'modified-priority',
                                     'value': u'mypriority'},
                                 {   'col': 'component',
                                     'style': 'modified-component',
                                     'value': u'mycomp'},
                                 {   'col': 'mycustomfield',
                                     'style': 'modified-mycustomfield',
                                     'value': u'mycustomfield1'}],
                    'style': ''},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': u'2'},
                                 {   'col': 'owner',
                                     'style': 'modified-owner',
                                     'value': u'you'},
                                 {   'col': 'priority',
                                     'style': 'modified-priority',
                                     'value': u'yourpriority'},
                                 {   'col': 'component',
                                     'style': 'modified-component',
                                     'value': u'yourcomp'},
                                 {   'col': 'mycustomfield',
                                     'style': 'modified-mycustomfield',
                                     'value': u'customfield2'}],
                    'style': ''},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'owner',
                                     'style': 'owner',
                                     'value': u'she'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'herpriority'},
                                 {   'col': 'component',
                                     'style': 'component',
                                     'value': u'hercomp'},
                                 {   'col': 'mycustomfield',
                                     'style': 'mycustomfield',
                                     'value': u'customfield3'}],
                    'style': 'color-new-even'}],
    'title': 'Preview Import'}

title = Preview Import
report {
  title = preview import
  headers {
    0 = ticket {
      real = ticket
    }
    1 = Summary {
      real = summary
    }
    2 = Owner {
      real = owner
    }
  }
  items {
    0 {
      __color__ = -new {
        hidden = 1
      }
      ticket-imported = (new)
      summary = Méthode
      owner = a&amp;'(è§&#34;(§èà)
    }
    1 {
      __color__ = -new {
        hidden = 1
      }
      ticket-imported = (new)
      summary = فرانصهي
      owner = ù'/?
    }
    2 {
      __color__ = -new {
        hidden = 1
      }
      ticket-imported = (new)
      summary = لوبنلن
      owner = me
    }
  }
  description = << EOM
<style type="text/css">
.ticket-imported, .modified-ticket-imported { width: 40px; }
.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-summary, .modified-owner { font-style: italic; }
</style>
<p>
Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.
</p>
<ul><li>3 tickets will be imported (3 added, 0 modified, 0 unchanged).
</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.
</li><li>Some Trac fields are not present in the import. They will default to:
</li></ul><blockquote>
<blockquote>
<table class="wiki">
<tr><td><strong>field</strong></td><td><strong>Default value</strong>
</td></tr><tr><td>Description, Cc, Milestone, Component, Url, Version, Mycustomfield, Keywords, Severity</td><td><i>(Empty value)</i>
</td></tr><tr><td>Status</td><td>new
</td></tr><tr><td>Changetime</td><td><i>(now)</i>
</td></tr><tr><td>Reporter</td><td>testuser
</td></tr><tr><td>Type</td><td>task
</td></tr><tr><td>Priority</td><td>major
</td></tr><tr><td>Time</td><td><i>(now)</i>
</td></tr><tr><td>Resolution</td><td><i>(None)</i>
</td></tr></table>
</blockquote>
</blockquote>
<p>
(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).
</p>
<ul><li>Some user names do not exist in the system: a&amp;'(è§"(§èà), ù'/?, me. Make sure that they are valid users.
</li></ul><br/><form action="importer" method="post"><input type="hidden" name="action" value="import" /><div class="buttons"><input type="submit" name="cancel" value="Cancel" /><input type="submit" value="Execute import" /></div></form>
EOM
  numrows = 3
  mode = list
}

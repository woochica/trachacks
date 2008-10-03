<h2>Manage Ticket Template</h2>

<form class="mod" id="modtemplate" method="post">
  <fieldset>
    <legend>チケットテンプレートの変更</legend>
    <div class="field">
      <label for="type">チケットの分類:</label><br />
      <select id="type" name="type">
        <?cs each:type = ticketext.template.types ?>
        <option value="<?cs var:type.name ?>" <?cs if:type.selected ?>selected="selected"<?cs /if ?>>
          <?cs var:type.name ?>
        </option>
        <?cs /each ?>
      </select>
    </div>
    <div class="field">
      <label for="template">テンプレートの内容(<a tabindex="42" href="<?cs var:$trac.href.wiki ?>/WikiFormatting">WikiFormatting</a>を使用できます):</label><br />
      <textarea id="template" name="template" class="wikitext" rows="10" cols="78" style="{width : 98%}"><?cs var:ticketext.template.template ?></textarea>
    </div>
  </fieldset>
  
  <br />
  
  <fieldset>
    <legend>利用するカスタムフィールド</legend>
    <?cs if:len(ticketext.template.customfields) ?>
    <table id="cflist" class="listing">
      <thead>
        <tr>
          <th class="sel">&nbsp;</th>
          <th>名前</th>
          <th>タイプ</th>
          <th>ラベル</th>
        </tr>
      </thead>
      <tbody>
        <?cs each:cf = ticketext.template.customfields ?>
        <tr>
          <td><input type="checkbox" name="cf-enable" value="<?cs var:cf.name ?>"
              <?cs if:cf.enable == 1 ?>checked="checked"<?cs /if ?> /></td>
          <td><?cs var:cf.name ?></td>
          <td><?cs var:cf.type ?></td>
          <td><?cs var:cf.label ?></td>
        </tr>
        <?cs /each ?>
      </tbody>
    </table>
    <?cs else ?>
      <p class="help">カスタムフィールドは定義されていません。</p>
    <?cs /if ?>    
  </fieldset>
  
  <script type="text/javascript" src="<?cs var:htdocs_location ?>js/wikitoolbar.js"></script>
  
  <div class="buttons">
    <input type="submit" value="変更を適用">
  </div>
</form>

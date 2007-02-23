<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav"></div>
<div id="content" class="testcase">

 <h1>Test-Case Management</h1>
    <div>
        <table>
            <?cs each:page_provider = testcase.page_providers_paths ?>
                <tr>
                    <td>
                        <a href="<?cs var:page_provider.path ?>" ><?cs var:page_provider.name ?></a>
                    </td>
                </tr>
            <?cs /each ?>
        </table>
    </div>
     <?cs if:testcase.page_template ?><?cs
       include testcase.page_template ?><?cs
      else ?><br/><br/><br/><?cs
       var:testcase.page_content ?><?cs
      /if ?>
          
  <br style="clear: right"/>
 </div>
</div>
<?cs include "footer.cs"?>
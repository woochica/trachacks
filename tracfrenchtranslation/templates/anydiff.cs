<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="changeset">
 <div id="title">
    <h1>Sélectionnez la base et la cible pour les différences :</h1>
 </div>

 <div id="anydiff">
  <form action="<?cs var:anydiff.changeset_href ?>" method="get">
   <table>
    <tr>
     <th><label for="old_path">De :</label></th>
     <td>
      <input type="text" id="old_path" name="old_path" value="<?cs
         var:anydiff.old_path ?>" size="44" />
      <label for="old_rev">à la révision :</label>
      <input type="text" id="old_rev" name="old" value="<?cs
         var:anydiff.old_rev ?>" size="4" />
     </td>
    </tr>
    <tr>
     <th><label for="new_path">À :</label></th>
     <td>
      <input type="text" id="new_path" name="new_path" value="<?cs
         var:anydiff.new_path ?>" size="44" />
      <label for="new_rev">à la révision:</label>
      <input type="text" id="new_rev" name="new" value="<?cs
         var:anydiff.new_rev ?>" size="4" />
     </td>
    </tr>
   </table>
   <div class="buttons">
      <input type="submit" value="Afficher les modifications" />
   </div>
  </form>
 </div>
 <div id="help">
  <strong>Remarque :</strong> Consultez la page <a href="<?cs var:trac.href.wiki
  ?>/TracChangeset#ExaminingDifferencesBetweenBranches">TracChangeset</a> pour plus d'informations
  sur l'utilisation de la fonction de différence.
 </div>
</div>

<?cs include "footer.cs"?>

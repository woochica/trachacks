<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="settings">

 <h1>Ustawienia i zarz±dzanie sesjami</h1>

 <h2>Ustawienia u¿ytkownika</h2>
 <p>
 Ta strona pozwoli zmodyfikowaæ ca³y serwis do Twoich potrzeb. Ustawienia sesji s± przechowywane przez serweri identyfikowane za pomoc± "klucza sesji" zapisanego w pliku cookie przegl±darki. Pozwoli to przywróciæ Twoje ustawienia 
 </p>
 <form method="post" action="">
 <div>
  <h3>Osobiste informcje</h3>
  <div>
   <input type="hidden" name="action" value="save" />
   <label for="name">Name:</label>
   <input type="text" id="name" name="name" class="textwidget" size="30"
          value="<?cs var:settings.name ?>" />
  </div>
  <div>
   <label for="email">Email:</label>
   <input type="text" id="email" name="email" class="textwidget" size="30"
          value="<?cs var:settings.email ?>" />
  </div><?cs
  if:settings.session_id ?>
   <h3>Session</h3>
   <div>
    <label for="newsid">Session Key:</label>
    <input type="text" id="newsid" name="newsid" class="textwidget" size="30"
           value="<?cs var:settings.session_id ?>" />
    <p>Klucz sesji u¿ywany jest do identyfikacji w³asnych ustawieñ i sesji na serwerze. 
    Automatycznie wygenerowany mo¿esz zmieniæ na co¶ ³atwiejszego do zapamiêtania, je¶li zamierzasz korzystaæ z innej przegl±darki.</p>
   </div><?cs
  /if ?>
  <div>
   <br />
   <input type="submit" value="Zapisz zmiany" />
  </div >
 </div>
</form><?cs
if:settings.session_id ?>
 <hr />
 <h2>Load Session</h2>
 <p>Mo¿esz wczytaæ poprzednio zapisan± sesjê wpisuj±c poni¿ej odpowiadaj±cy jej klucz sesji nastêpnie klikaj±c 'Od¶wie¿'. Pozwoli to Tobie u¿ywaæ tych samych ustawieñ na wielu komputerach i/lub przegl±darkach.</p>
 <form method="post" action="">
  <div>
   <input type="hidden" name="action" value="load" />
   <label for="loadsid">Existing Session Key:</label>
   <input type="text" id="loadsid" name="loadsid" class="textwidget" size="30"
          value="" />
   <input type="submit" value="Od¶wie¿" />
  </div>
 </form><?cs
/if ?>

</div>
<?cs include:"footer.cs"?>

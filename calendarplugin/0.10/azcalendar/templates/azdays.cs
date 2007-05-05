<?cs # -*-coding:utf-8-*- ?><?cs
def:dayname(number) ?><?cs
    if:#number == #0 ?>Po<?cs
    elif:#number == #1 ?>Út<?cs
    elif:#number == #2 ?>St<?cs
    elif:#number == #3 ?>Čt<?cs
    elif:#number == #4 ?>Pá<?cs
    elif:#number == #5 ?>So<?cs
    elif:#number == #6 ?>Ne<?cs
    else ?>Day <?cs var:number ?><?cs
    /if ?><?cs
/def ?><?cs

def:monthname(number) ?><?cs
    if:#number == #0 ?>Leden<?cs
    elif:#number == #1 ?>Únor<?cs
    elif:#number == #2 ?>Březen<?cs
    elif:#number == #3 ?>Duben<?cs
    elif:#number == #4 ?>Květen<?cs
    elif:#number == #5 ?>Červen<?cs
    elif:#number == #6 ?>Červenec<?cs
    elif:#number == #7 ?>Srpen<?cs
    elif:#number == #8 ?>Září<?cs
    elif:#number == #9 ?>Říjen<?cs
    elif:#number == #10 ?>Listopad<?cs
    elif:#number == #11 ?>Prosinec<?cs
    else ?>Month <?cs var:number ?><?cs
    /if ?><?cs
/def ?>


<?cs # -*-coding:utf-8-*- ?><?cs
def:dayname(number) ?><?cs
    if:#number == #0 ?>Mon<?cs
    elif:#number == #1 ?>Tue<?cs
    elif:#number == #2 ?>Wed<?cs
    elif:#number == #3 ?>Thu<?cs
    elif:#number == #4 ?>Fri<?cs
    elif:#number == #5 ?>Sat<?cs
    elif:#number == #6 ?>Sun<?cs
    else ?>Day <?cs var:number ?><?cs
    /if ?><?cs
/def ?><?cs

def:monthname(number) ?><?cs
    if:#number == #0 ?>January<?cs
    elif:#number == #1 ?>February<?cs
    elif:#number == #2 ?>March<?cs
    elif:#number == #3 ?>April<?cs
    elif:#number == #4 ?>May<?cs
    elif:#number == #5 ?>June<?cs
    elif:#number == #6 ?>July<?cs
    elif:#number == #7 ?>August<?cs
    elif:#number == #8 ?>September<?cs
    elif:#number == #9 ?>October<?cs
    elif:#number == #10 ?>November<?cs
    elif:#number == #11 ?>December<?cs
    else ?>Month <?cs var:number ?><?cs
    /if ?><?cs
/def ?>


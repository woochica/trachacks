# --------------------------------------------------------------------------------------------------------------------------

def get_piece(line,terminator=[':'],strip=[' ','\n','\t','\f']):			     	 
  piece     = ''			        									        
  remainder = ''													        
  															        
  state = 'idle'													        
  					       
  for c in line:													        
    if (state=='idle'): 												        
      if (c in [' ','\n','\t','\f']):
  	continue
      else:
  	state = 'piece'
  	piece = ''
  	
    if (state=='piece'):												        
      if (c=='"'):
  	state = 'doublequoted'
      elif (c == "'"):
  	state = 'singlequoted'
      elif (c in terminator):
  	# terminator found...
  	state = 'remainder'
      elif (c not in strip):
  	piece += c
    elif (state == 'doublequoted'):											        
      if (c == '"'):
  	state = 'piece'
      else:
  	piece += c
    elif (state == 'singlequoted'):											        
      if (c == "'"):
  	state = 'piece'
      else:
  	piece += c
    elif (state=='remainder'):												        
      remainder += c

  return piece,remainder												        

# --------------------------------------------------------------------------------------------------------------------------  

def parse_options(options,default):			     
  result   = default						     
  options += ' ' # ensure that last option is terminated...	     

  state      = 'idle'						     
  force_xtra = False						     

  for c in options:						     
    if (state=='idle'): 					     
      if (c in [' ',':','\n','\f']):
  	# skip...
  	if (c==':'):
  	  force_xtra = True
  	continue
      else:
  	state = 'name'
  	name  = ''
  	
    if (state=='name'): 					     
      if (c=='"'):
  	state = 'doublequotedname'
      elif (c == "'"):
  	state = 'singlequotedname'
      elif (c=='='):
  	state = 'value'
  	value = ''
      elif (c in [' ',':','\n','\f']):
  	# terminator found...
  	if ((name not in result['cfg']) or (force_xtra==True)):
  	  result['xtras'].append(name)
  	  result['xtra' ][name]=''
  	else:
  	  result['cfg'  ][name]=''
  	  
  	if (c==':'):
  	  force_xtra = True

  	state = 'idle'
      else:
  	name += c
    elif (state == 'doublequotedname'): 			     
      if (c == '"'):
  	state = 'name'
      else:
  	name += c
    elif (state == 'singlequotedname'): 			     
      if (c == "'"):
  	state = 'name'
      else:
  	name += c
    elif (state=='value'):					     
      if (c=='"'):
  	state = 'doublequotedvalue'
      elif (c == "'"):
  	state = 'singlequotedvalue'
      elif (c in [' ',':','\n','\f']):
  	# terminator found...
  	if ((name not in result['cfg']) or (force_xtra==True)):
  	  result['xtras'].append(name)
  	  result['xtra' ][name]=value
  	else:
  	  result['cfg'  ][name]=value

  	if (c==':'):
  	  force_xtra = True

  	state = 'idle'
      else:
  	value += c
    elif (state == 'doublequotedvalue'):			     
      if (c == '"'):
  	state = 'value'
      else:
  	value += c
    elif (state == 'singlequotedvalue'):			     
      if (c == "'"):
  	state = 'value'
      else:
  	value += c

  return result 						     

# --------------------------------------------------------------------------------------------------------------------------

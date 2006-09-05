#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#


#A very simple method to escape values going into SQL queries
def dbEscape(text):
    if isinstance(text, int):
    	return str(text)
    return text.replace("'", "''")

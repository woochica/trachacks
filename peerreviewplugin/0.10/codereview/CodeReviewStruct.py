#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

from codereview.dbEscape import dbEscape

class CodeReviewStruct(object):
    "Stores a Code Review Entry"

    #Individual CodeReview ID Number
    IDReview = ""

    #Author's username
    Author = ""

    #Status of a code review
    Status = ""

    #Date created (using Trac's internal representation)
    DateCreate = 0

    #Name of the CodeReview
    Name = ""

    #Author's notes
    Notes = ""

    def __init__(self, row):
        if(row != None):
            #initialize variables
            self.IDReview = `row[0]`
            self.Author = row[1]
            self.Status = row[2]
            self.DateCreate = row[3]
            self.Name = row[4]
            self.Notes = row[5]

    def save(self, db):
        query = ""
        cursor = db.cursor()
        #Add information to a new database entry
        if self.IDReview == "":
            query = "INSERT INTO CodeReviews VALUES(NULL,'" + dbEscape(self.Author) + "','" + dbEscape(self.Status) + "','" + `self.DateCreate` + "','" + dbEscape(self.Name) + "','" + dbEscape(self.Notes) + "')"
            cursor.execute(query)
            db.commit()
            cursor.execute("SELECT last_insert_rowid() FROM CodeReviews")
            self.IDReview = `cursor.fetchone()[0]`
        else:
        #Update information in existing database entry
            query = "UPDATE CodeReviews SET Author = '" + dbEscape(self.Author) + "', Status = '" + dbEscape(self.Status) + "', DateCreate = '" + `self.DateCreate` + "', Name = '" + dbEscape(self.Name) + "', Notes = '" + dbEscape(self.Notes) +  "' WHERE IDReview = '" + dbEscape(self.IDReview) + "'"
            cursor.execute(query)
            db.commit()
        return self.IDReview
    

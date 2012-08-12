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

class ReviewerStruct(object):
    "Stores a Reviewer Entry"

    #Reviewer's assigned CodeReview ID number
    IDReview = ""

    #Reviewer's username
    Reviewer = ""

    #Status of the reviewer's voting capability
    Status = ""

    #Reviewer's vote
    Vote = "-1"

    def __init__(self, row):
        if(row != None):
            #initialize variables
            self.IDReview = `row[0]`
            self.Reviewer = row[1]
            self.Status = row[2]
            self.Vote = `row[3]`

    def save(self, db):
        #Add information to a new database entry
        query = "INSERT INTO Reviewers VALUES('" + dbEscape(self.IDReview) + "', '" + dbEscape(self.Reviewer) + "','" + dbEscape(self.Status) + "','" + dbEscape(self.Vote) + "')"
        cursor = db.cursor();
        try:
            cursor.execute(query)
            db.commit()
        except:
            #Update information in existing database entry
            query = "UPDATE Reviewers SET Status = '" + dbEscape(self.Status) + "', Vote = '" + dbEscape(self.Vote) + "' WHERE IDReview = '" + dbEscape(self.IDReview) + "' AND Reviewer = '" + dbEscape(self.Reviewer) + "'"
            cursor.execute(query)
            db.commit()

# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Team5 
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

class ReviewerStruct(object):
    "Stores a Reviewer Entry"

    #Reviewer's assigned CodeReview ID number
    IDReview = ""

    #Reviewer's username
    Reviewer = ""

    #Status of the reviewer's voting capability
    Status = 0

    #Reviewer's vote
    Vote = "-1"

    def __init__(self, row):
        if row != None:
            #initialize variables
            self.IDReview = row[0]
            self.Reviewer = row[1]
            self.Status = row[2]
            self.Vote = row[3]

    def save(self, db):
        try:
            #Add information to a new database entry
            cursor = db.cursor();
            cursor.execute("""
                INSERT INTO Reviewers (IDReview, Reviewer, Status, Vote)
                VALUES (%s, %s, %s, %s)""",
                (self.IDReview, self.Reviewer, self.Status, self.Vote))
            db.commit()
        except:
            #Update information in existing database entry
            cursor = db.cursor();
            cursor.execute("""
                UPDATE Reviewers SET Status=%s, Vote=%s
                WHERE IDReview=%s AND Reviewer=%s""",
                (self.Status, self.Vote, self.IDReview, self.Reviewer))
            db.commit()

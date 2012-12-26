# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Team5 
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

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
        if row != None:
            #initialize variables
            self.IDReview = row[0]
            self.Author = row[1]
            self.Status = row[2]
            self.DateCreate = row[3]
            self.Name = row[4]
            self.Notes = row[5]

    def save(self, db):
        if self.IDReview == "":
            #Add information to a new database entry
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO CodeReviews (Author, Status, DateCreate, Name, Notes)
                VALUES (%s, %s, %s, %s, %s)""",
                (self.Author, self.Status, self.DateCreate, self.Name, self.Notes))
            self.IDReview = db.get_last_id(cursor, 'CodeReviews', 'IDReview')
            db.commit()
        else:
            #Update information in existing database entry
            cursor = db.cursor()
            cursor.execute("""
                UPDATE CodeReviews SET Author=%s, Status=%s, DateCreate=%s,
                  Name=%s, Notes=%s WHERE IDReview=%s""",
                (self.Author, self.Status, self.DateCreate, self.Name, self.Notes, self.IDReview))
            db.commit()
        return self.IDReview

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

class ReviewCommentStruct(object):
    "Stores a ReviewComment Entry"

    #Individual comment ID number
    IDComment = "-1"

    #File ID to which the comment belongs
    IDFile = ""

    #Comment ID of the comment's heirarchical parent
    IDParent = "-1"

    #Line number the ID refers to
    LineNum = ""

    #Author of the comment
    Author = ""

    #Comment's text
    Text = ""

    #Attachment name and path
    AttachmentPath = ""

    #Date comment created
    DateCreate = -1

    #Collection of comment IDs belonging to the comment's heirarchical children
    Children = {}

    def __init__(self, row):
        if(row != None):
            #initialize variables
            self.IDComment = row[0]
            self.IDFile = row[1]
            self.IDParent = row[2]
            self.LineNum = row[3]
            self.Author = row[4]
            self.Text = row[5]
            self.AttachmentPath = row[6]
            self.DateCreate = row[7]
            self.Children = {}

    def save(self, db):
        cursor = db.cursor()
        #Add information to a new database entry
        if self.IDComment == "-1":
            query = "INSERT INTO ReviewComments VALUES(NULL,'" + dbEscape(self.IDFile) + "', '" + dbEscape(self.IDParent) + "','" + dbEscape(self.LineNum) + "','" + dbEscape(self.Author) + "','" + dbEscape(self.Text) + "','" + dbEscape(self.AttachmentPath) + "','" + `self.DateCreate` + "')"
            cursor.execute(query)
            db.commit()
            self.IDComment = cursor.lastrowid;
        else:
        #Update information in existing database entry
            query = "UPDATE ReviewComments SET IDFile = '" + dbEscape(self.IDFile) + "', IDParent = '" + dbEscape(self.IDParent) + "', LineNum = '" + dbEscape(self.LineNum) + "', Author = '" + dbEscape(self.Author) + "', Text = '" + dbEscape(self.Text) + "', AttachmentPath = '" + dbEscape(self.AttachmentPath) + "', DateCreate = '" + `self.DateCreate` + "' WHERE IDComment = '" + dbEscape(self.IDComment) + "'"
            cursor.execute(query)
            db.commit()
        return self.IDComment

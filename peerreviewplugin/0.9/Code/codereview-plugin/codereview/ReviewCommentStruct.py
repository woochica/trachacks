# Copyright (C) 2006 Gabriel Golcher
# Copyright (C) 2006 Michael Kuehl
# All rights reserved.
#
# This file is part of The Trac Peer Review Plugin
#
# The Trac Peer Review Plugin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# The Trac Peer Review Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with The Trac Peer Review Plugin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
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
            self.IDComment = `row[0]`
            self.IDFile = `row[1]`
            self.IDParent = `row[2]`
            self.LineNum = `row[3]`
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
            cursor.execute("SELECT last_insert_rowid() FROM ReviewComments")
            self.IDComment = `cursor.fetchone()[0]`
        else:
        #Update information in existing database entry
            query = "UPDATE ReviewComments SET IDFile = '" + dbEscape(self.IDFile) + "', IDParent = '" + dbEscape(self.IDParent) + "', LineNum = '" + dbEscape(self.LineNum) + "', Author = '" + dbEscape(self.Author) + "', Text = '" + dbEscape(self.Text) + "', AttachmentPath = '" + dbEscape(self.AttachmentPath) + "', DateCreate = '" + `self.DateCreate` + "' WHERE IDComment = '" + dbEscape(self.IDComment) + "'"
            cursor.execute(query)
            db.commit()
        return self.IDComment

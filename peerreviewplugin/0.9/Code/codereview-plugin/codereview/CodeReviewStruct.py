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
    

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

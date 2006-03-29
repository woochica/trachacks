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

class ReviewFileStruct(object):
    "Stores a ReviewFile Entry"

    #Individual CodeReview's attached file ID number
    IDFile = ""

    #CodeReview ID (to which the file belongs to)
    IDReview = ""

    #Path and name of the file commented on
    Path = ""

    #Starting line for the code snippet requiring comments
    LineStart = ""

    #Ending line for the code snippet requiring comments
    LineEnd = ""

    #Version of the file in the repository
    Version = ""

    def __init__(self, row):
        if(row != None):
            #initialize variables
            self.IDFile = `row[0]`
            self.IDReview = `row[1]`
            self.Path = row[2]
            self.LineStart = `row[3]`
            self.LineEnd = `row[4]`
            self.Version = `row[5]`

    def save(self, db):
        cursor = db.cursor()
        if self.IDFile == "":
        #Add information to a new database entry
            query = "INSERT INTO ReviewFiles VALUES(NULL,'" + dbEscape(self.IDReview) + "', '" + dbEscape(self.Path) + "','" + dbEscape(self.LineStart) + "','" + dbEscape(self.LineEnd) + "','" + dbEscape(self.Version) + "')"
            cursor.execute(query)
            db.commit()
            cursor.execute("SELECT last_insert_rowid() FROM ReviewFiles")
            self.IDFile = `cursor.fetchone()[0]`
        else:
        #Update information in existing database entry
            query = "UPDATE ReviewFiles SET IDReview = '" + dbEscape(self.IDReview) + "', Path = '" + dbEscape(self.Path) + + "', LineStart = '" + dbEscape(self.LineStart) + "', LineEnd = '" + dbEscape(self.LineEnd) + "', Version = '" + dbEscape(self.Version) + "' WHERE IDFile = '" + dbEscape(self.IDFile) + "'"
            cursor.execute(query)
            db.commit()
        return self.IDFile

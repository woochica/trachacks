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
            self.IDFile = row[0]
            self.IDReview = row[1]
            self.Path = row[2]
            self.LineStart = row[3]
            self.LineEnd = row[4]
            self.Version = row[5]

    def save(self, db):
        cursor = db.cursor()
        if self.IDFile == "":
        #Add information to a new database entry
            cursor.execute("INSERT INTO ReviewFiles "
                           "(IDReview, Path, LineStart, LineEnd, Version) "
                           "VALUES (%s, %s, %s, %s, %s) ",
                           (self.IDReview, self.Path, self.LineStart, self.LineEnd, self.Version))
            self.IDFile = db.get_last_id(cursor, 'ReviewFiles', 'IDFile')
            db.commit()
        else:
        #Update information in existing database entry
            cursor.execute("UPDATE ReviewFiles SET "
                           "IDReview=%s, Path=%s, LineStart=%s, LineEnd=%s, Version=%s WHERE IDFile=%s",
                           (self.IDReview, self.Path, self.LineStart, self.LineEnd, self.Version, self.IDFile))
            db.commit()
        return self.IDFile

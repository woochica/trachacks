#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

from trac.core import *
from trac.db.schema import Table, Column, Index

# Version of Code Review schema
version = 1

#The tables for the Code Review Plugin
tables = [
    Table('CodeReviews', key='IDReview')[
        Column('IDReview', auto_increment=True),
        Column('Author'),
        Column('Status'),
        Column('DateCreate', type='int'),
        Column('Name'),
        Column('Notes'),
    ],
    Table('Reviewers', key=('IDReview', 'Reviewer'))[
        Column('IDReview', type='int'),
        Column('Reviewer'),
        Column('Status', type='int'),
        Column('Vote', type='int'),
    ],
    Table('ReviewFiles', key='IDFile')[
        Column('IDFile', auto_increment=True),
        Column('IDReview', type='int'),
        Column('Path'),
        Column('LineStart', type='int'),
        Column('LineEnd', type='int'),
        Column('Version', type='int'),
    ],
    Table('ReviewComments', key='IDComment')[
        Column('IDComment', auto_increment=True),
        Column('IDFile', type='int'),
        Column('IDParent', type='int'),
        Column('LineNum', type='int'),
        Column('Author'),
        Column('Text'),
        Column('AttachmentPath'),
        Column('DateCreate', type='int'),
    ],
]

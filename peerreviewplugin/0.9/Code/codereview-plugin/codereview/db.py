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

from trac.core import *
from trac.db_default import Table, Column, Index

# Version of Code Review schema
version = 1


#The tables for the Code Review Plugin
schema = [
    Table('CodeReviews', key='IDReview')[
        Column('IDReview', auto_increment=True),
	Column('Author'),
	Column('Status'),
	Column('DateCreate', type='int'),
	Column('Name'),
        Column('Notes')],
    Table('Reviewers', key=('IDReview', 'Reviewer'))[
	Column('IDReview', type='int'),
	Column('Reviewer'),
	Column('Status', type='int'),
	Column('Vote', type='int')],
    Table('ReviewFiles', key='IDFile')[
	Column('IDFile', auto_increment=True),
	Column('IDReview', type='int'),
	Column('Path'),
	Column('LineStart', type='int'),
	Column('LineEnd', type='int'),
	Column('Version', type='int')],
    Table('ReviewComments', key='IDComment')[
	Column('IDComment', auto_increment=True),
	Column('IDFile', type='int'),
	Column('IDParent', type='int'),
	Column('LineNum', type='int'),
	Column('Author'),
	Column('Text'),
	Column('AttachmentPath'),
	Column('DateCreate', type='int')],
]

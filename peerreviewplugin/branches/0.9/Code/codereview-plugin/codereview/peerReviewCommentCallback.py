#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

import time
import os
import shutil
import urllib
from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.web.main import IRequestHandler
from trac import util
from trac.util import escape, Markup
from codereview.dbBackend import *
from trac.web.chrome import add_stylesheet


class UserbaseModule(Component):
    implements(IRequestHandler, ITemplateProvider)
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewCommentCallback'

    #This page should never be called directly.  It should only be called
    #by javascrpit HTTPRequest calls.
    def process_request(self, req):
        if not (req.perm.has_permission('CODE_REVIEW_MGR') or req.perm.has_permission('CODE_REVIEW_DEV')):
            req.hdf['invalid'] = 4
            return 'peerReviewCommentCallback.cs', None


	req.hdf['invalid'] = 0
        req.hdf['trac.href.peerReviewCommentCallback'] = self.env.href.peerReviewCommentCallback()
        actionType = req.args.get('actionType')

        if actionType == 'addComment':
            self.createComment(req)
        
        elif actionType == 'getCommentTree':
            self.getCommentTree(req)

        elif actionType == 'getCommentFile':
            self.getCommentFile(req)
            
        else:
            req.hdf['invalid'] = 5

        return 'peerReviewCommentCallback.cs', None
                
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]

    #Used to send a file that is attached to a comment
    def getCommentFile(self, req):
        req.hdf['invalid'] = 6
        shortPath = req.args.get('fileName')
        idFile = req.args.get('IDFile')
        if idFile == None or shortPath == None:
            return
       
       	shortPath = urllib.unquote(shortPath)
        self.path = os.path.join(self.env.path, 'attachments', 'CodeReview', urllib.quote(idFile))
        self.path = os.path.normpath(self.path)
        attachments_dir = os.path.join(os.path.normpath(self.env.path),'attachments')
        commonprefix = os.path.commonprefix([attachments_dir, self.path])
        assert commonprefix == attachments_dir
        fullPath = os.path.join(self.path,shortPath)
        req.send_header('Content-Disposition', 'attachment; filename=' + shortPath)
        req.send_file(fullPath)        

    #Creates a comment based on the values from the request
    def createComment(self, req):
        req.hdf['invalid'] = 5
        struct = ReviewCommentStruct(None)
        struct.IDParent = req.args.get('IDParent')
        struct.IDFile = req.args.get('IDFile')
        struct.LineNum = req.args.get('LineNum')
        struct.Author = util.get_reporter_id(req)
        struct.Text = req.args.get('Text')
        struct.DateCreate = int(time.time())

        if (struct.IDFile == None) or (struct.LineNum == None) or (struct.Author == None) or (struct.Text == None):
            return
        if (struct.IDFile == "") or (struct.LineNum == "") or (struct.Author == ""):
            return
        if (struct.Text == ""):
            return
        if (struct.IDParent == None or struct.IDParent == ""):
            struct.IDParent = "-1"

        #If there was a file uploaded with the comment, place it in the correct spot
        #The basic parts of this code were taken from the file upload portion of
        #the trac wiki code
	
	if req.args.has_key('FileUp'):
   	     upload = req.args['FileUp']
             if upload.filename:
                 self.path = os.path.join(self.env.path, 'attachments', 'CodeReview', urllib.quote(struct.IDFile))
                 self.path = os.path.normpath(self.path) 
                 size = 0
                 if hasattr(upload.file, 'fileno'):
                     size = os.fstat(upload.file.fileno())[6]
                 else:
                     size = upload.file.len
                 if size != 0:
                     filename = urllib.unquote(upload.filename)
                     filename = filename.replace('\\', '/').replace(':', '/')
                     filename = os.path.basename(filename)
                     import sys, unicodedata
                     if sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 3):
                         filename = unicodedata.normalize('NFC',unicode(filename,'utf-8')).encode('utf-8')
                     attachments_dir = os.path.join(os.path.normpath(self.env.path),'attachments')
                     commonprefix = os.path.commonprefix([attachments_dir, self.path])
                     assert commonprefix == attachments_dir
                     if not os.access(self.path, os.F_OK):
                         os.makedirs(self.path)
                     path, targetfile = util.create_unique_file(os.path.join(self.path,filename))
                     try:
                         shutil.copyfileobj(upload.file, targetfile)
                         struct.AttachmentPath = os.path.basename(path)
                     finally:
                         targetfile.close()
                    
        struct.save(self.env.get_db_cnx())

    #Returns a comment tree for the requested line number
    #in the requested file
    def getCommentTree(self, req):
        IDFile = req.args.get('IDFile')
        LineNum = req.args.get('LineNum')
        if (IDFile == None) or (LineNum == None):
            req.hdf['invalid'] = 1
            return
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        comments = dbBack.getCommentsByFileIDAndLine(IDFile, LineNum)
        commentHtml = ""
        first = True
        keys = comments.keys()
        keys.sort();
        for key in keys:
            if not comments.has_key(comments[key].IDParent):
                commentHtml += self.buildCommentHTML(comments[key], 0, LineNum, IDFile, first)
                first = False;
        if commentHtml == "":
            commentHtml = "No Comments on this Line"
        req.hdf['lineNum'] = LineNum
        req.hdf['fileID'] = IDFile
        req.hdf['commentHTML'] = Markup(commentHtml) 

    #Recursively builds the comment html to send back.
    def buildCommentHTML(self, comment, nodesIn, LineNum, IDFile, first):
        if nodesIn > 50:
            return ""

        childrenHTML = ""
        keys = comment.Children.keys()
        keys.sort();
        for key in keys:
            child = comment.Children[key]
            childrenHTML += self.buildCommentHTML(child, nodesIn+1, LineNum, IDFile, False)
               
        factor = 15
        width = (5+nodesIn*factor);
        
        html = "<table width=\"400px\" style=\"border-collapse: collapse\" id=\"" + comment.IDParent + ":" + comment.IDComment + "\">"
        if not first:
            html += "<tr><td width=\"" + `width` + "px\"></td>"
            html += "<td colspan=\"3\" width=\"" + `(400-width)` + "px\" style=\"border-top: 1px solid #C0C0C0;\"></td></tr>"
        html += "<tr><td width=\"" + `width` + "px\"></td>"
        html += "<td colspan=\"2\" align=\"left\" width=\"" + `(400-100-width)` + "px\">Author: " + comment.Author + "</td>"
        html += "<td width=\"100px\" align=\"right\">" + util.format_date(comment.DateCreate) + "</td></tr>"
        html += "<tr><td width=\"" + `width` + "px\"></td><td valign=\"top\" width=\"" + `factor` + "px\" id=\"" + comment.IDComment + "TreeButton\">"
        if not childrenHTML == "":
            html += "<img src=\"" + self.env.href.chrome() + "/hw/images/minus.gif\" onclick=\"collapseComments(" + comment.IDComment + ");\">"
        html += "</td>"
        html += "<td colspan=\"2\" align=\"left\" width=\"" + `(400-width-factor)` + "px\" bgcolor=\"#F7F7F0\" style=\"border: 1px solid #999999\">" + comment.Text + "</td></tr>"
        html += "<tr><td width=\"" + `width` + "px\"></td><td width=\"" + `factor` + "px\"></td>"
        html += "<td width=\"" + `(400-100-factor-width)` + "px\" align=\"left\">"
        if comment.AttachmentPath != "":
            html += "<a border=0 alt=\"Code Attachment\"  href=\"" + self.env.href.peerReviewCommentCallback() + "?actionType=getCommentFile&fileName=" + comment.AttachmentPath + "&IDFile=" + IDFile + "\"><img src=\"" + self.env.href.chrome() + "/hw/images/paper_clip.gif\"> " +  comment.AttachmentPath + "</a>"
        html += "</td>"
        html += "<td width=\"100px\" align=\"right\">"
        html += "<a href=\"javascript:addComment(" + LineNum + ", " + IDFile + ", " +  comment.IDComment + ")\">Reply</a></td></tr>"
        html += "<tr height=\"3\"><td width=\"" + `width` + "px\"></td><td width=\"" + `factor` + "px\"></td><td width=\"" + `(400-width-factor)` + "px\" colspan=\"2\"></td></tr>"
        html += "</table>"

        html += childrenHTML
        return html


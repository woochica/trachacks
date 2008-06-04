#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#
#

# Code Review plugin
# This class handles the display for the perform code review page
# The file contents are taken from the respository and converted to
# an HTML friendly format.  The line annotator customizes the
# repository browser's line number to indicate what lines are being
# reviewed and if there are any comments on a particular line.

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac import util
from trac.util import escape
from codereview.dbBackend import *
from trac.web.chrome import add_stylesheet
from trac.versioncontrol.web_ui.util import *
from trac.web.chrome import add_link, add_stylesheet
import string

from genshi.builder import tag

class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IHTMLPreviewAnnotator)

    #global variables for the line annotator
    comments = {}
    fileID = -1
    imagePath = ''
    lineStart = -1
    lineEnd = -1
    
    # ITextAnnotator methods
    def get_annotation_type(self):
    	return 'performCodeReview', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        return None

    #line annotator for Perform Code Review page
    #if line has a comment, places an icon to indicate comment
    #if line is not in the rage of reviewed lines, it makes
    #the color a light gray
    def annotate_row(self, context, row, lineno, line, data):
        htmlImageString = '<img src="' + self.imagePath + '">'
        #make line number light gray
        if(lineno <= self.lineEnd and lineno >= self.lineStart):
            #if there is a comment on this line
            if(self.comments.has_key(lineno)):
                #if there is more than 0 comments
                if(self.comments[lineno] > 0):
                    return row.append(tag.th(id='L%s' % lineno)(tag.a(tag.img(src='%s' % self.imagePath) + ' ' + str(lineno), href='javascript:getComments(%s, %s)' % (lineno, self.fileID))))
            return row.append(tag.th(id='L%s' % lineno)(tag.a(lineno, href='javascript:addComment(%s, %s, -1)' % (lineno, self.fileID))))
        return row.append(tag.th(id='L%s' % lineno)(tag.font(lineno, color='#CCCCCC')))

    #def annotate_line(self, number, content):
    #    htmlImageString = '<img src="' + self.imagePath + '">'
    #    #make line number light gray
    #    if(number <= self.lineEnd and number >= self.lineStart):
    #        #if there is a comment on this line
    #        if(self.comments.has_key(number)):
    #            #if there is more than 0 comments
    #            if(self.comments[number] > 0):
    #                return ('<th id="L%s"><a href="javascript:getComments(%s, %s)">' % (number, number, self.fileID)) + htmlImageString + ('&nbsp;%s</a></th>' % (number))
    #        return '<th id="L%s"><a href="javascript:addComment(%s, %s, -1)">%s</a></th>' % (number, number, self.fileID, number)
    #    return '<th id="L%s"><font color="#CCCCCC">%s</font></th>' % (number, number)
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'
                
    def get_navigation_items(self, req):
        return []
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/peerReviewPerform'
                                        
    def process_request(self, req):
        if req.perm.has_permission('CODE_REVIEW_MGR'):
            req.hdf['manager'] = 1
        else:
            req.perm.assert_permission('CODE_REVIEW_DEV')
            req.hdf['manager'] = 0

        #get some link locations for the template
        req.hdf['trac.href.peerReviewMain'] = self.env.href.peerReviewMain()
        req.hdf['trac.href.peerReviewNew'] = self.env.href.peerReviewNew()
        req.hdf['trac.href.peerReviewSearch'] = self.env.href.peerReviewSearch()
        req.hdf['trac.href.peerReviewOptions'] = self.env.href.peerReviewOptions()

        #for top-right navigation links
        req.hdf['main'] = "no"
        req.hdf['create'] = "no"
        req.hdf['search'] = "no"
        req.hdf['options'] = "no"

        #get the fileID from the request arguments
        idFile = req.args.get('IDFile')
        self.fileID = idFile
        #if the file id is not set - display an error message
	if idFile == None:
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "File ID Error"
            req.hdf['error.message'] = "No file ID given - unable to load page."
            return 'error.cs', None

        #get the database
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        #get all the comments for this file
        self.comments = dbBack.getCommentDictForFile(idFile)
        #get the file properties from the database
        resultFile = dbBack.getReviewFile(idFile)
        #make the thumbtac image global so the line annotator has access to it
        self.imagePath = self.env.href.chrome() + '/hw/images/thumbtac11x11.gif'
        #get image and link locations
        req.hdf['trac.href.peerReviewCommentCallback'] = self.env.href.peerReviewCommentCallback()
        req.hdf['trac.href.peerReviewView'] = self.env.href.peerReviewView()
        req.hdf['trac.htdocs.thumbtac'] = self.imagePath
        req.hdf['trac.htdocs.plus'] = self.env.href.chrome() + '/hw/images/plus.gif'
        req.hdf['trac.htdocs.minus'] = self.env.href.chrome() + '/hw/images/minus.gif'

        #if the file is not found in the database - display an error message
        if resultFile == None:
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "File ID Error"
            req.hdf['error.message'] = "Unable to locate given file ID in database."
            return 'error.cs', None

        #get the respository
        repos = self.env.get_repository(req.authname)
        #get the file attributes
        req.hdf['review.path'] = resultFile.Path
        req.hdf['review.version'] = resultFile.Version
        req.hdf['review.lineStart'] = resultFile.LineStart
        req.hdf['review.lineEnd'] = resultFile.LineEnd
        req.hdf['review.reviewID'] = resultFile.IDReview
        #make these global for the line annotator
        self.lineEnd = resultFile.LineEnd
        self.lineStart = resultFile.LineStart

        #if the repository can't be found - display an error message
        if(repos == None):
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Subversion Repository Error"
            req.hdf['error.message'] = "Unable to acquire subversion repository."
            return 'error.cs', None

        #get the correct location - using revision number and repository path
        try:
            node = get_existing_node(self.env, repos, resultFile.Path, resultFile.Version)
        except:
            youngest_rev = repos.youngest_rev
            node = get_existing_node(self.env, repos, resultFile.Path, youngest_rev)

        #if the node can't be found - display error message
        if(node == None):
            req.hdf['error.type'] = "TracError"
            req.hdf['error.title'] = "Subversion Node Error"
            req.hdf['error.message'] = "Unable to locate subversion node for this file."
            return 'error.cs', None

        # Generate HTML preview - this code take from Trac - refer to their documentation
        mime_type = node.content_type
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = get_mimetype(node.name) or mime_type or 'text/plain'

        ctpos = mime_type.find('charset=')
        if ctpos >= 0:
            charset = mime_type[ctpos + 8:]
        else:
            charset = None

        mimeview = Mimeview(self.env)
        path = req.args.get('path', '/')
        rev = None
        content = node.get_content().read(mimeview.max_preview_size)
        if not is_binary(content):
            if mime_type != 'text/plain':
                plain_href = self.env.href.peerReviewBrowser(node.path, rev=rev and node.rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text', 'text/plain')

        #assign the preview to a variable for clearsilver
        context = Context.from_request(req, 'source', path, node.created_rev)
        req.hdf['file'] =  mimeview.preview_data(context, content, len(content),
                                                 mime_type, node.created_path,
                                                 None,
                                                 annotations=['performCodeReview'])

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')	

        return 'peerReviewPerform.cs', None
                
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    #gets the directory where the htdocs are stored - images, etc.
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]

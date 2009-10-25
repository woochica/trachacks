from trac.core import *
from trac.web.api import ITemplateStreamFilter,IRequestFilter
from trac.perm import IPermissionRequestor

from model import Review

from genshi.builder import tag
from genshi.filters import Transformer

class ChangeSetReview(Component):
    """
    Add change set review properties
    """
       
    implements(ITemplateStreamFilter, IRequestFilter,IPermissionRequestor)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'changeset.html':
                changeset = data.get('changeset')
                filter = Transformer('//dd[@class="message searchable"]')
                return stream | filter.after(self._review_attrs(req,changeset))
        return stream

    def author(self, changeset):
        if changeset.author == '':
            return "anonymous"
        else:
            return changeset.author

    def _review_attrs(self, req, changeset):
        review = Review.get(self.env.get_db_cnx(),changeset.rev, self.author(changeset))
        if req.perm.has_permission('CODE_REVIEW'):
            comment = tag.textarea(review.comment, name="review_comment", rows=6, cols=100 )
            if review.status=="ACCEPTED":
                checkbox = tag.input(type="checkbox", name="review_passed", checked="true")
            else:
                checkbox = tag.input(type="checkbox", name="review_passed")
            submit = tag.input(type="hidden", name="review_rev", value=changeset.rev)+ \
                tag.input(type="hidden", name="review_author", value=self.author(changeset))+ \
                tag.input(type="submit", name="review", value="Review")
        else:
            comment = tag.span(review.comment)
            checkbox = tag.span(review.status)
            submit = "";
        return tag.form(
                        tag.dt("Reviewer:",class_="property author"),
                        tag.dd( req.authname,class_="author"),
                        tag.dt("Comment:",class_="property author"),
                        tag.dd( comment ),       
                        tag.dt("Passed:",class_="property author"),
                        tag.dd(checkbox+submit)
                        )       

    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/changeset') and 'review' in req.args:
            review = Review.get(self.env.get_db_cnx(),req.args['review_rev'],req.args['review_author'])
            review.author = req.args['review_author']
            review.reviewer =  req.authname
            review.comment = req.args['review_comment']
            review.status = "REJECTED"
            if 'review_passed' in req.args:
                review.status = "ACCEPTED"
            review.save(self.env.get_db_cnx())
        return handler;

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        return template, content_type;
    
    def get_permission_actions(self):
        return ["CODE_REVIEW"]

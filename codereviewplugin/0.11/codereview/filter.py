from trac.core import *
from trac.web.api import ITemplateStreamFilter,IRequestFilter

from model import Review

from genshi.builder import tag
from genshi.filters import Transformer

class ChangeSetReview(Component):
    """
    Add change set review properties
    """
       
    implements(ITemplateStreamFilter, IRequestFilter)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'changeset.html':
                changeset = data.get('changeset')
                filter = Transformer('//dd[@class="message searchable"]')
                return stream | filter.after(self._review_attrs(req,changeset))
        return stream

    def _review_attrs(self, req, changeset):
        review = Review.get(self.env.get_db_cnx(),changeset.rev)
        if review.status=="ACCEPTED":
            checkbox = tag.input(type="checkbox", name="review_passed", checked="true")
        else:
            checkbox = tag.input(type="checkbox", name="review_passed")
        return tag.form(
                        tag.dt("Reviewer:",class_="property author"),
                        tag.dd("viola",class_="author"),
                        tag.dt("Comment:",class_="property author"),
                        tag.dd( tag.textarea(review.comment, name="review_comment", rows=6, cols=100 )),       
                        tag.dt("Passed:",class_="property author"),
                        tag.dd(checkbox+
                               tag.input(type="hidden", name="review_rev", value=changeset.rev)+
                               tag.input(type="submit", name="review", value="Review"))
                        )       

    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/changeset') and 'review' in req.args:
            review = Review.get(self.env.get_db_cnx(),req.args['review_rev'])
            review.reviewer = "viola"
            review.comment = req.args['review_comment']
            review.status = "REJECTED"
            if 'review_passed' in req.args:
                review.status = "ACCEPTED"
            review.save(self.env.get_db_cnx())
        return handler;

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        return template, content_type;

# -*- coding: utf-8 -*-

from acct_mgr.web_ui import RegistrationModule
from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer
from trac.core import Component, implements, TracError
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_warning
from trac.web.main import IRequestFilter
from trac.config import Option


class QuestionRegistrationModule(Component):
    implements(ITemplateStreamFilter, IRequestFilter)
    env = log = config = None # make pylint happy
    question = Option('registerquestion', 'question',
        doc='Question to be answered for the registration to succeed')
    answer = Option('registerquestion', 'answer',
        doc='The right answer to the registration question')
    hint = Option('registerquestion', 'hint',
        doc='The warning message/hint for the question')

    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith('/register') and (
            req.method == 'GET' or
            'registration_error' in data):
            question = None
            if self.question is not None and len(self.question)>0:
                question = tag.label(
                    tag(self.question + " "),
                    tag.input(id='question', type='text', name='question')
                    )
            # First Fieldset of the registration form XPath match
            xpath_match = '//form[@id="acctmgr_registerform"]/fieldset[1]'
            if question is None:
                return stream
            else:
                return stream | Transformer(xpath_match). \
                    append(tag(Markup(question)))
        # Admin Configuration
        elif req.path_info.startswith('/admin/accounts/config'):
            api_html = tag.div(
                tag.label("Question:", for_="registerquestion_question") +
                tag.input(class_="textwidget", name="question",
                          value=self.question, size=60)
            ) + tag.div(
                tag.label("Answer:", for_="registerquestion_answer") +
                tag.input(class_="textwidget", name="answer",
                          value=self.answer, size=60)
            ) + tag.div(
                tag.label("Hint:", for_="registerquestion_hint") +
                tag.input(class_="textwidget", name="hint",
                          value=self.hint, size=60)
            ) + tag.br()


            # First fieldset of the Account Manager config form
            xpath_match = '//form[@id="accountsconfig"]/fieldset[1]'

            return stream | Transformer(xpath_match). \
                before(tag.fieldset(tag.legend("Anti-Robot Question For Registration") + api_html))
        return stream

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if isinstance(handler, RegistrationModule):
            if req.method == 'POST' and req.args.get('action') == 'create' and req.args.get('question').strip().lower() != self.answer.strip().lower():
                add_warning(req, self.hint)
                req.environ['REQUEST_METHOD'] = 'GET'
                req.args.pop('password', None)
                req.args.pop('password_confirm', None)

        # Admin Configuration
        if req.path_info.startswith('/admin/accounts/config') and \
            req.method == 'POST':
            self.config.set('registerquestion', 'question',
                            req.args.get('question'))
            self.config.set('registerquestion', 'answer',
                            req.args.get('answer'))
            self.config.set('registerquestion', 'hint',
                            req.args.get('hint'))
            self.config.save()
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == "register.html":
            if "acctmgr" not in data:
                data["acctmgr"] = {}
        return template, data, content_type

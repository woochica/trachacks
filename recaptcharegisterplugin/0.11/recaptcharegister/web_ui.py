from acct_mgr.web_ui import RegistrationModule
from trac.web.main import IRequestHandler, IRequestFilter
from trac.config import ConfigurationError, Option
from recaptcha.client import captcha


class RecaptchaRegistrationModule(RegistrationModule):
    public_key = Option('recaptcha', 'public_key',
        doc='The public key given to you from the reCAPTCHA site')
    private_key = Option('recaptcha', 'private_key',
        doc='The private key given to you from the reCAPTCHA site')

    def check_config(self):
        if not self.public_key or not self.private_key:
            raise ConfigurationError('public_key and private_key needs ' \
                'to be in the [captcha] section of your trac.ini file. ' \
                'Get these keys from http://recaptcha.net/')

    # IRequestHandler methods
    def process_request(self, req):
        ret = super(RecaptchaRegistrationModule, self).process_request(req)
        h, data, n = ret
        return "recaptcharegister.html", data, n


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler


    def post_process_request(self, req, template, data, content_type):
        print "T", template
        if template not in ['recaptcharegister.html']:
            return (template, data, content_type)

        self.check_config()

        html = captcha.displayhtml(self.public_key)
        #req.hdf.set_unescaped('recaptcha_javascript', html)
        data['recaptcha_javascript'] = html

        return (template, data, content_type)


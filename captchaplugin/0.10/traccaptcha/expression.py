import random
from trac.core import *
from trac.config import *
from trac.util.html import html, Markup
from traccaptcha import ICaptchaGenerator


class ExpressionCaptcha(Component):
    """ Implementation of a captcha in the form of a human readable numeric
    expression. Initial implementation by sergeych@tancher.com. """

    implements(ICaptchaGenerator)

    terms = IntOption('numeric-captcha', 'terms', 3,
            """ Number of terms in expression. """)
    ceiling = IntOption('numeric-captcha', 'ceiling', 10,
            """ Maximum value of individual terms in expression. """)

    operations = {'*': 'multiplied by', '-': 'minus', '+': 'plus'}
    numerals = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
                'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
                'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen',
                'nineteen' )
    tens = ('twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
            'eighty', 'ninety')

    # ICaptchaGenerator methods
    def generate_captcha(self, req):
        if self.ceiling > 100:
            raise TracError('Numeric captcha can not represent numbers > 100')
        terms = [str(random.randrange(0, self.ceiling)) for _ in xrange(self.terms)]
        operations = [random.choice(self.operations.keys()) for _ in xrange(self.terms)]
        expression = sum(zip(terms, operations), ())[:-1]
        expression = eval(compile(' '.join(expression), 'captcha_eval', 'eval'))
        human = sum(zip([self.humanise(int(t)) for t in terms],
                        [self.operations[o] for o in operations]), ())[:-1]
        return (expression, html.p('Calculate the answer to the following question:')(
                                   html.blockquote(' '.join(map(str, human)))))

    # Internal methods
    def humanise(self, value):
        if value < 20:
            return self.numerals[value]
        english = self.tens[value / 10 - 2]
        if value % 10:
            english += ' ' + self.numerals[value % 10]
        return english

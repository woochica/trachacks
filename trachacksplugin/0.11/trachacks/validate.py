"""
Form validation for Genshi.

First a couple of forms:

>>> from genshi import HTML
>>> html = HTML('''
... <body>
...   <form id="user">
...     <input type="text" name="name"/>
...     <input type="text" name="age"/>
...     <input type="submit" id="create" value="Create user"/>
...   </form>
...   <form id="controls">
...     <input type="submit" name="delete"/>
...     <input type="submit" name="copy"/>
...   </form>
... </body>
... '''.strip())

Then some fake POST data:

>>> data = {'name': 'Alec', 'age': '12'}

Finally we define our form. Validation for fields is built up from a set of
discrete aspects we wish to validate:

>>> form = Form('user')
>>> form.add('name', MinLength(6), 'Name must be at least 6 characters.')
>>> form.add('age', Chain(int, Min(18)), 'Age must be an integer > 18.')

Now we validate the input:

>>> fields, errors = form.validate(data)
>>> fields
{}
>>> print '\\n'.join(map(repr, sorted(errors.items())))
('age', 'Age must be an integer > 18.')
('name', 'Name must be at least 6 characters.')

Oops. Let's inform the user:

>>> print html | form.inject_errors(errors)
<body>
  <form id="user">
    <input type="text" name="name"/><div class="error">Name must be at least 6 characters.</div>
    <input type="text" name="age"/><div class="error">Age must be an integer &gt; 18.</div>
    <input type="submit" id="create" value="Create user"/>
  </form>
  <form id="controls">
    <input type="submit" name="delete"/>
    <input type="submit" name="copy"/>
  </form>
</body>

Then imagine they've corrected their input:

>>> data['name'] = 'Alec Thomas'
>>> data['age'] = '18'
>>> fields, errors = form.validate(data)
>>> sorted(fields.items())
[('age', 18), ('name', 'Alec Thomas')]
>>> errors
{}

Better.
"""

import re
from genshi.builder import tag
from genshi.filters.transform import Transformer


"""
class UserForm(Schema):
    user = Field('Name must be at least 6 characters'', [MinLength(6)])
    age = Field('Age must be an integer > 18.', [int, Min(18)])
"""

class ValidationError(Exception):
    pass


class Chain(object):
    def __init__(self, *aspects):
        self.aspects = aspects

    def __call__(self, value):
        for aspect in self.aspects:
            value = aspect(value)
        return value


class Range(object):
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def __call__(self, value):
        assert self.min is None or value >= self.min
        assert self.max is None or value <= self.max
        return value


class Min(Range):
    def __init__(self, min):
        super(Min, self).__init__(min=min)


class Max(Range):
    def __init__(self, max):
        super(Max, self).__init__(max=max)


class Length(Range):
    def __call__(self, value):
        super(Length, self).__call__(len(value))
        return value


class MinLength(Length):
    def __init__(self, min):
        super(MinLength, self).__init__(min=min)


class MaxLength(Length):
    def __init__(self, max):
        super(MaxLength, self).__init__(max=max)


class Pattern(object):
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def __call__(self, value):
        assert self.pattern.match(value)
        return value


class Empty(object):
    def __call__(self, value):
        assert not value
        return value


class AnyOf(object):
    def __init__(self, *values):
        self.values = values

    def __call__(self, value):
        assert value in self.values
        return value


class Not(object):
    def __init__(self, aspect):
        self.aspect = aspect

    def __call__(self, value):
        try:
            self.aspect(value)
            raise ValidationError()
        except:
            return value


class FormInjector(object):
    """Insert messages into a Genshi stream."""

    def __init__(self, form, errors):
        self.form = form
        self.errors = errors

    def __call__(self, stream):
        for name, message in self.errors.items():
            field = self.form[name]
            message = field.format_error(message)
            transform = Transformer('//form[@id="%s"]' % self.form.id) \
                        .select(field.path).attr('class', 'error')
            transform = getattr(transform, field.where)(message)
            stream |= transform
        return stream


class Field(object):
    def __init__(self, name, aspect=None, message='Invalid field.', hint=None,
                 path=None, where='after'):
        self.name = name
        self.message = message
        self.aspect = aspect or (lambda v: v)
        self.path = path
        self.where = where
        self.hint = hint
        if self.path is None:
            self.path = '//input[@name="%(name)s"] | ' \
                        '//textarea[@name="%(name)s"] | ' \
                        '//select[@name="%(name)s"]' % {'name': name}

    def validate(self, value):
        return self.aspect(value)

    def format_error(self, message=None):
        return tag.div(message or self.message, class_='error')

    def format_hint(self, hint=None):
        return tag.div(hint or self.hint, class_='hint')


class Form(object):
    def __init__(self, id, fields=None, injector=FormInjector):
        self.id = id
        self.injector = injector
        if fields:
            self.fields = dict((v.name, v) for v in fields)
        else:
            self.fields = {}

    def __getitem__(self, key):
        return self.fields[key]

    def __setitem__(self, key, value):
        value.name = key
        self.fields[key] = value

    def __delitem__(self, key):
        del self.fields[key]

    def add(self, name, *args, **kwargs):
        """Add a new Field."""
        if isinstance(name, Field):
            self.fields[name.name] = name
        else:
            self.fields[name] = Field(name, *args, **kwargs)

    def inject_errors(self, errors):
        return self.injector(self, errors)

    def validate(self, data):
        """Validate the given data.

        Returns a tuple of (fields, errors) where both are dictionaries
        mapping field names to text.
        """
        fields = {}
        errors = {}
        for name, field in self.fields.items():
            value = data.get(name, '')
            try:
                fields[name] = field.validate(value)
            except Exception, e:
                errors[name] = field.message
        return fields, errors


if __name__ == '__main__':
    import doctest
    doctest.testmod()

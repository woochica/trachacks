"""
example of a CustomFieldProvider
"""

from interface import ICustomFieldProvider
from trac.core import *

class SampleCustomFieldProvider(Component):
    implements(ICustomFieldProvider)

    def fields(self):
        return { 'foo': { 'label': 'My custom field' } }

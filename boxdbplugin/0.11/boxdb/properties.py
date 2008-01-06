# Created by  on 2008-01-02.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *

from boxdb.api import IDocumentPropertyRenderer

class PropertyBase(Component):
    """Base class to simplify making new property renderers."""

    abstract = True

    implements(IDocumentPropertyRenderer)

    # IDocumentPropertyRenderer methods
    def get_properties(self):
        name = self.__class__.__name__.lower()
        if name.endswith('property'):
            name = name[:-8]
        yield name

    def decode_property(self, name, values):
        return values

    def encode_propery(self, name, value):
        return value

    def render_property(self, name, value):
        return str(value)


class StringProperty(PropertyBase):
    """A simple string property, also the default property type."""

    def decode_property(self, name, values):
        return values[0]

    def encode_property(self, name, value):
        yield value


class NumberProperty(PropertyBase):
    """A simple number property."""

    def decode_property(self, name, values):
        return int(values[0])

    def encode_property(self, name, value):
        yield str(value)

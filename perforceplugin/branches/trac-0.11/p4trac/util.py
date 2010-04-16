"""Utilities for Perforc Trac plugin."""

__all__ = ['AutoAttributesMeta']

class AutoAttributesMeta(type):
    """A meta class that automatically converts methods with names of the
    form '_[get/set/del/doc]_<name>' into descriptors with the name '<name>'.

    Example::
     | class Foo(object):
     |
     |    __metaclass__ = AutoAttributes
     |
     |    def _get_value(self):
     |      return 1
     |
     |    _doc_value = "Returns the value 1."
     |
     | f = Foo()
     | assert f.value == 1
    """

    def __new__(cls, name, bases, members):

        props = set()

        # First pass to find all the properties
        for member in members.keys():
            if len(member) > 5:
                if member.startswith('_get_'):
                    props.add(member[5:])
                elif member.startswith('_set_'):
                    props.add(member[5:])
                elif member.startswith('_del_'):
                    props.add(member[5:])

        # Second pass to replace the members with properties
        for prop in props:
            fget = members.pop('_get_%s' % prop, None)
            fset = members.pop('_set_%s' % prop, None)
            fdel = members.pop('_del_%s' % prop, None)
            doc = members.pop('_doc_%s' % prop, None)
            if doc is None:
                if fget and hasattr(fget, '__doc__'):
                    doc = fget.__doc__
                elif fset and hasattr(fset, '__doc__'):
                    doc = fset.__doc__
                elif fdel and hasattr(fdel, '__doc__'):
                    doc = fdel.__doc__
            members[prop] = property(fget, fset, fdel, doc)
            
        return type.__new__(cls, name, bases, members)

class FastTemporaryFile(object):
    """A file-like stream object for writing temporary data efficiently.

    Stores the file contents in-memory for small files and uses a
    temporary file on the file system for large files (the temporary
    file is cleaned up when the stream is closed). You may read/write from
    this file as you would a normal file object.
    """

    __slots__ = ['_stream', '_isFile', '_smallFileSize']
    
    def __init__(self, smallFileSize=65536):

        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO

        self._stream = StringIO.StringIO()
        self._isFile = False
        self._smallFileSize = int(smallFileSize)
        
    def write(self, data):
        if not self._isFile:
            if self._stream.tell() + len(data) > self._smallFileSize:
                # We are about to go over the small file size limit
                # Move all the contents out to a temporary file and continue
                # writing there.
                from tempfile import TemporaryFile
                fstream = TemporaryFile()
                self._stream.seek(0)
                fstream.writelines(self._stream)
                self._stream.close()
                self._stream = fstream
                self._isFile = True
        self._stream.write(data)

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            stream = object.__getattribute__(self, '_stream')
            return getattr(stream, name)

def toUnicode(value, defaultCodec='utf8'):
    """Convert a value to unicode.

    If the string is already a unicode string returns it unchanged.
    Otherwise decodes it to a unicode string using the specified codec.
    """
    if isinstance(value, unicode):
        return value
    elif isinstance(value, str):
        return unicode(value, defaultCodec)
    else:
        return unicode(value)

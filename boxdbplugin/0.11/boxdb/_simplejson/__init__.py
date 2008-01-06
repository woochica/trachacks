__version__ = '1.7'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONEncoder',
]

from decoder import JSONDecoder
from encoder import JSONEncoder

_default_encoder = JSONEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    encoding='utf-8'
)

def dump(obj, fp, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None, encoding='utf-8',
        **kw):
    # cached encoder
    if (skipkeys is False and ensure_ascii is True and
        check_circular is True and allow_nan is True and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and not kw):
        iterable = _default_encoder.iterencode(obj)
    else:
        if cls is None:
            cls = JSONEncoder
        iterable = cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, indent=indent,
            encoding=encoding, **kw).iterencode(obj)
    # could accelerate with writelines in some versions of Python, at
    # a debuggability cost
    for chunk in iterable:
        fp.write(chunk)


def dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None, separators=None,
        encoding='utf-8', **kw):
    # cached encoder
    if (skipkeys is False and ensure_ascii is True and
        check_circular is True and allow_nan is True and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and not kw):
        return _default_encoder.encode(obj)
    if cls is None:
        cls = JSONEncoder
    return cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, encoding=encoding,
        **kw).encode(obj)

_default_decoder = JSONDecoder(encoding=None, object_hook=None)

def load(fp, encoding=None, cls=None, object_hook=None, **kw):
    return loads(fp.read(),
        encoding=encoding, cls=cls, object_hook=object_hook, **kw)

def loads(s, encoding=None, cls=None, object_hook=None, **kw):
    if cls is None and encoding is None and object_hook is None and not kw:
        return _default_decoder.decode(s)
    if cls is None:
        cls = JSONDecoder
    if object_hook is not None:
        kw['object_hook'] = object_hook
    return cls(encoding=encoding, **kw).decode(s)



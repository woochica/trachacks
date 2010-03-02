# util.py

def pretty_err(req, title, message=None):
    req.hdf['error.type'] = 'TracError'
    req.hdf['error.title'] = title
    req.hdf['title'] = title
    if message:
        req.hdf['error.message'] = message
    else:
        req.hdf['error.message'] = title
    return 'error.cs', None

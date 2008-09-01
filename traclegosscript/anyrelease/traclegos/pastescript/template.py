from paste.script import templates

var = templates.var

class TracProject(templates.Template):
    _template_dir = 'template'
    summary = 'configuration for a trac project'
    vars = [
        var('file', 'file to templatize'),
        var('path', 'relative path to file', default=None),
        var('description', 'One-line description of the package'),
        var('author', 'Author name'),
        var('author_email', 'Author email'),
        var('url', 'URL of homepage'),
        ] 

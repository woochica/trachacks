from paste.script import templates

var = templates.var

class TracQuickPluginTemplate(templates.Template):
    _template_dir = 'template'
    summary = "Another paste template for a trac plugin, like TracPluginTemplateScript"
    vars = [
        var('description', 'Oneline description of the plugin'),
        var('package_code', 'Package codename, should be lower case, and unique from other plugins'),
        var('author', 'Author name'),
        var('author_email', 'Author email'),
        ] 

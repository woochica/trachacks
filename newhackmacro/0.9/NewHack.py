# vim: expandtab
from StringIO import StringIO
from string import Template
from trac.util import TracError
from trac.wiki import wiki_to_html
from trac.wiki import WikiPage
import trac.perm
import re, string, svn, os, time
import fcntl

SVN_URL = 'http://trac-hacks.org/svn/'

# Production configuration
SVN_LOCAL_PATH = 'file:///var/svn/trachacks010' #TODO: get this from [trac]:repository_dir (or [repositories] on Trac 0.12+)
SVN_PERMISSIONS = '/var/svn/trachacks010-permissions' #TODO: get this from [trac]:authz_file
BASE_URL = "/"

# Test configuration
#SVN_LOCAL_PATH = 'file:///home/athomas/projects/trac/env/svn/'
#SVN_PERMISSIONS = '/home/athomas/projects/trac/env/permissions'
#BASE_URL = "/trachacks/"

tag_cache = {}

def fetch_page(cursor, page):
    cursor.execute("SELECT text FROM wiki WHERE name=%s ORDER BY version DESC LIMIT 1", (page,))
    text = cursor.fetchone()
    if not text:
        raise TracError("No such template page <a class='missing' href='%s/wiki/%s'>%s</a>" % (page, BASE_URL, page))
    return text[0]

def expand_vars(text, vars):
    s = Template(text)
    return s.substitute(vars)

def get_branch_values(hdf, branch):
    out = []
    o = hdf.getObj(branch)
    if not o: return out
    if o.value():
        out.append(o.value())
    else:
        o = o.child()
        while o:
            out.append(o.value())
            o = o.next()
    return out

def generate_vars(hdf):
    vars = {}
    vars['OWNER'] = hdf.getValue('trac.authname', 'anonymous')
    vars['WIKINAME'] = hdf.getValue('args.name', 'NoPage')
    if not vars['WIKINAME'].lower().endswith(hdf.getValue('args.type', '')):
        vars['WIKINAME'] += hdf.getValue('args.type', '').title()
    vars['TITLE'] = hdf.getValue('args.title', ' '.join(re.findall('[A-Z][a-z]+', vars['WIKINAME'])))
    vars['LCNAME'] = vars['WIKINAME'].lower()
    vars['TYPE'] = hdf.getValue('args.type', '')
    vars['SOURCEURL'] = SVN_URL + vars['LCNAME']
    vars['DESCRIPTION'] = hdf.getValue('args.description', 'No description available')
    vars['EXAMPLE'] = hdf.getValue('args.example', 'No example available')
    return vars

def execute(hdf, template, env):
    out = StringIO()
    errors = []
    authname = hdf.getValue("trac.authname", "anonymous")
    if not template:
        raise TracError("No template page supplied")
    if authname == "anonymous":
        errors.append('You need to <a href="%s">register</a> then <a href="%s">login</a> in order to create a new hack.' % (hdf.getValue("trac.href.registration", ""), hdf.getValue("trac.href.login", "")))
    db = env.get_db_cnx()
    cursor = db.cursor()

    # Fetch meta-data from tags
    META_TAGS = set()
    from tractags.api import TagEngine
    wikitags = TagEngine(env).tagspace.wiki
    for tag in wikitags.get_tagged_names(['metatag']):
        META_TAGS.update(wikitags.get_tagged_names([tag]))
    TYPES = wikitags.get_tagged_names(['type'])
    RELEASES = wikitags.get_tagged_names(['release'])

    page_name = hdf.getValue('args.name', '')
    if not page_name.lower().endswith(hdf.getValue('args.type', '')):
        page_name += hdf.getValue('args.type', '').title()
    page_title = hdf.getValue('args.title', '')
    page_description = hdf.getValue('args.description', '')
    page_example = hdf.getValue('args.example', '')
    page_type = hdf.getValue('args.type', 'plugin')
    page_tags = get_branch_values(hdf, 'args.tags')
    page_releases = get_branch_values(hdf, 'args.releases')
    page_preview = hdf.getValue('args.previewhack', '')
    page_create = hdf.getValue('args.createhack', '')

    def write_tags(out, tags, checked = (), name = "tags", type="checkbox"):
        count = 0
        for tag in sorted(tags):
            if tag.startswith('tags/'):
                continue
            (linktext,title,desc) = getInfo(db,tag)
            link = env.href.wiki(tag)
            check = ""
            if tag in checked:
                check = " checked"
            out.write('<input type="%s" name="%s" value="%s"%s/> <a href="%s" title="%s">%s</a>&nbsp;&nbsp;\n' % (type, name, tag, check, link, title, tag))
            count += 1
            if count % 8 == 0:
                out.write("<br/>\n")
        return count

    # Validation
    if page_preview or page_create:
        try:
            fetch_page(cursor, page_name)
        except:
            pass
        else:
            errors.append("Page name %s already exists" % page_name)
        if not re.match('^([A-Z][a-z]+){2,}$', page_name): errors.append('Invalid WikiName, only alpha characters are accepted and must be CamelCase')
        if not page_name: errors.append("No WikiName provided")
        if not page_title: errors.append("No page title provided")
        if not page_type: errors.append('No page type selected')
        if not page_description: errors.append("No description provided")
        if not page_example: errors.append("No example provided")
        if not page_releases: errors.append("No releases selected")

    if page_create and not errors:
        import subprocess
        repos_dir = env.config.get('trac', 'repository_dir')
        cursor.execute("SELECT name FROM component WHERE name=%s", (page_name,))
        row = cursor.fetchone()
        if row:
            errors.append("Component '%s' already exists" % page_name)
        if subprocess.call(["svn", "ls", "%s/%s" % (SVN_LOCAL_PATH, page_name.lower())]) == 0:
            errors.append("Repository path '%s' already exists" % page_name.lower())
        if not os.access(SVN_PERMISSIONS, os.W_OK):
            errors.append("Can't write to Subversion permissions file")

        lockfile = open("/var/tmp/newhack.lock", "w")
        try:
            rv = fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if rv:
                errors.append('Failed to acquire lock, received error code %i' % rv)
        except IOError:
            errors.append('A hack is currently being created by another user. Try again later.')

        if not errors:
            try:
                # Insert component
                cursor.execute('INSERT INTO component (name, owner) VALUES (%s, %s)', (page_name, authname))
                # Create page
                page = WikiPage(env, page_name, db = db)
                page.text = expand_vars(fetch_page(cursor, template), generate_vars(hdf))
                out.write('Created wiki page.<br>\n')
                # Creating SVN paths
                paths = ['%s/%s' % (SVN_LOCAL_PATH, page_name.lower())]
                for release in page_releases:
                    paths.append("%s/%s/%s" % (SVN_LOCAL_PATH, page_name.lower(), release))
                output = os.popen('/usr/bin/op create-hack %s "New hack %s, created by %s" %s 2>&1' % (authname, page_name, authname, ' '.join(paths))).readlines()
                if output:
                    raise Exception("Failed to create Subversion paths:\n%s" % ''.join(output))
                out.write("Created SVN layout.<br>\n")
                # Add SVN permissions
                perms = open(SVN_PERMISSIONS, "a")
                perms.write("\n[/%s]\n%s = rw\n" % (page_name.lower(), authname))
                out.write('Added SVN write permission.<br>\n')
                out.write('\nFinished.<p><h1>Hack Details</h1>\n')
                for release in page_releases:
                    svnpath = "%s%s/%s" % (SVN_URL, page_name.lower(), release)
                    out.write('The Subversion repository path for %s is <a href="%s">%s</a>.<br>\n' % (release, svnpath, svnpath))
                out.write('The page for your hack is <a href="%s">%s</a>.<br>\n' % (env.href.wiki(page_name), page_name))
                page.save(authname, 'New hack %s, created by %s' % (page_name, authname), None)
                db.commit()
                # Add tags
                env.log.debug(vars)
                tags = [page_type, authname] + page_tags + page_releases
                env.log.debug(tags)
                wikitags.replace_tags(None, page_name, tags)
                # Finish up
                rv = fcntl.flock(lockfile, fcntl.LOCK_UN)
                return out.getvalue()
            except Exception, e:
                # TODO Roll back changes to SVN_PERMISSIONS file
                db.rollback()
                rv = fcntl.flock(lockfile, fcntl.LOCK_UN)
                env.log.error(e, exc_info=True)
                raise TracError(str(e))

    out.write("""
<form name="newhack" id="edit" method="get" action="%(base_url)swiki/NewHack#preview" name="newhackform">
<!-- <fieldset id="changeinfo">
<legend>Register a new Trac Hack</legend> -->

<fieldset>
    <legend>Basic information</legend>
    <div class="field">
      <label for="name" title="WikiName of hack, eg. SubWiki"><strong>WikiName of hack</strong></label>
      <br/>
      <input id="name" title="WikiName of hack, eg. SubWiki" name="name" type="text" size="32" maxlength="32" value="%(name)s"/>
    </div>
    <br/>
    <div class="field">
      <label for="title" title="Full title of page, eg. Table of Contents Macro"><strong>Page title</strong></label>
      <br/>
      <input id="title" title="Full title of page, eg. Table of Contents Macro" name="title" type="text" size="64" value="%(title)s"/>
    </div>
    <br/>
    <div class="field">
        <label for="description"><strong>Description</strong></label>
        <br/>
        <textarea class="wikitext" id="description" name="description" cols="80" rows="8" title="Comprehensive description of your hack">%(description)s</textarea>
    </div>
</fieldset>
<br/>
<fieldset>
    <legend>Classification</legend>
    <div class="field">
        <label for="type" title="Type of hack"><strong>Type</strong></label>
        <br/>
        The type that best describes your hack. The title-cased version of the type will be appended to your page name.
        <br/>
""" % {
        'name' : hdf.getValue('args.name', ''),
        'title' : page_title,
        'description' : page_description,
        'base_url' : BASE_URL,
    })

    if not write_tags(out, TYPES, [page_type], "type", "radio"):
        raise TracError("No hack types available")

    out.write("""
    </div>
    <br/>
    <div class="field">
        <label for="release" title="Trac Releases this hack works with"><strong>Trac Release Compatibility</strong></label>
        <br/>
""")

    if not page_releases: page_releases = [ '0.12' ]
    if not write_tags(out, RELEASES, page_releases, "releases"):
        raise TracError("No Trac releases available")

    out.write("""
</div>
<br/>
<div class="field">
  <label for="release"><strong>Associated tags</strong></label>
  <br/>
  Additional tags for classifying your hack.
  <br />
""")

    cursor.execute("SELECT DISTINCT tag FROM tags WHERE tagspace='wiki'")
    if not write_tags(out, [x[0] for x in cursor.fetchall() or [] if x[0] not in META_TAGS and x[0].lower() == x[0]], page_tags):
        out.write("<i>No additional tags available.</i>")

    out.write("""
</div>
</fieldset>
<br/>
<fieldset>
    <legend>Miscellaneous information</legend>
<div class="field">
    <label for="example"><strong>Example usage</strong></label>
    <br/>One or more examples illustrating how to use your hack, if appropriate.
    <br/>
    <textarea class="wikitext" id="example" name="example" cols="80" rows="8" title="Example of your hack in 'action'">%(example)s</textarea>
</div>
</fieldset>
<div class="buttons">
 <input type="submit" name="createhack" value="Register new Trac Hack" />&nbsp;
 <input type="submit" name="previewhack" value="Preview" onSubmit="alert('foo')"/>
 <input type="submit" name="cancel" value="Cancel" />
</div>
</form>
    """ % {
        'example' : page_example
    })

    out.write("<div id='preview'></div>\n")
    if errors:
        for error in errors:
            out.write('<div class="system-message"><strong>Error:</strong> %s</div>\n' % error)
            
    if page_preview:
        out.write("""
<fieldset>
<legend>Preview of %s</legend>
""" % page_name)
        try:
            out.write(wiki_to_html(expand_vars(fetch_page(cursor, template), generate_vars(hdf)), env, None, db))
        except KeyError, e:
            raise TracError("Can't expand variable %s - fix the template page <a href='%s'>%s</a>" % (e, env.href.wiki(template), template))
        out.write("""
</fieldset>
""")

    return out.getvalue()

def getInfo(db,tag):
    global tag_cache
    if tag in tag_cache:
        return tag_cache[tag]
    cs = db.cursor()
    desc = tag
    # Get the latest revision only.
    cs.execute('SELECT text from wiki where name = %s order by version desc limit 1', (tag,))
    csrow = cs.fetchone()
    prefix = ''

    if csrow != None:
        text = csrow[0]
        m  = re.search('=+\s([^=]*)=+',text)
        if m != None:
            desc = string.strip(m.group(1))
    else:
        prefix = "Create "

    title = StringIO()
    title.write("%s%s"%(prefix, desc))
    if prefix != '' or desc == tag:
       desc = ''

    tag_cache[tag] = (tag, title.getvalue(), desc)
    return (tag,title.getvalue(),desc)

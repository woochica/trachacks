from trac.core import *
import trac.wiki.api as wiki
import trac.web.api as web
import trac.wiki.model as model

import sre

#============================================================
# The configuration section. Don't change this! (really).
#============================================================
GLOSSARY_CONFIG_SECTION = "glossary"


#============================================================
# The prefix under which glossary pages are to be found.
# config: glossary_prefix
#============================================================
GLOSSARY_PREFIX = "Glossary"

#============================================================
# The name of the index page, unprefixed.
# config: glossary_index
#============================================================
GLOSSARY_INDEX  = "Index"

#============================================================
# The name of the user identified as author for automatic
# page creation. If set to the string 'author', the author of
# the page being edited/ created will be used.
# config: glossary_author
#============================================================
GLOSSARY_AUTHOR = "automatic"


#============================================================
# The URL which can be used to rebuild the glossary index.
# config: glossary_rebuild_url
#============================================================
GLOSSARY_REBUILD_URL = "rebuild_glossary_index"


#============================================================
# Where automatically-generated links to the index are placed
# Top or Bottom, or None (string "None" or value None)
# config: glossary_index_link_placement
#============================================================
GLOSSARY_AUTO_INDEX_LINK_PLACEMENT = "Top"


def findOrCreateIndex(env, prefix, name, author):
  fullname = "/".join([prefix, name])
  #===========================================================
  # XXX: Race condition? If two threads are updating at the same
  # time, a conflict may occur. Best to raise an exception,
  # perhaps, and notify the user somehow (how?)
  # Actually it seems like the regular 'save' method raises
  # the standard 'page being modified by someone else' exception
  # which is caught and displayed to the user. This is kinda
  # ugly, since the user may not know that it is the index
  # causing the problem. Better to catch that exception at save
  # time and simply not create/ update the index, and document
  # it as a feature. So, er, it's a feature :)
  #============================================================
  index = GlossaryIndexPage(env, fullname)
  if index.version == 0:
    index.createIndex(prefix, name, author)
  return index


class GlossaryIndexPage(model.WikiPage):

  ENTRY_FORMAT = " * [wiki:%s %s]\r\n"
  ENTRY_RE     = sre.compile(" \* \[wiki:([\w/]+) ([^\]]+)\]")

  def createIndex(self, prefix, name, author, comment = "Automatically created index", remote_addr = '127.0.0.1' ):
    """
      Creates the index content if it does not exist.
    """
    url = self.env.config.get(GLOSSARY_CONFIG_SECTION, 'rebuild_url') or GLOSSARY_REBUILD_URL

    text = "= %s %s =\r\n[%s Rebuild]\r\n" % (prefix, name, self.env.href.wiki(url))

    charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for letter in charset[:13]:
      text += " [wiki:%s/%s#%s %s] " % (prefix, name, letter, letter)

    text += "\r\n"

    for letter in charset[13:]:
      text += " [wiki:%s/%s#%s %s] " % (prefix, name, letter, letter)

    text += "\r\n"


    for letter in charset:
      text += "== %s ==\r\n" % letter
    self.text = text
    self.save(author, comment, remote_addr)


  def addPageLink(self, link_to, author):
    """
      Updates the index content with a link to the specified glossary page.
    """
    name = link_to.name[link_to.name.find('/')+1:]
    initial = name[0].upper()

    begin = self.text.find("== %s ==" % initial)
    if initial < 'Z':
      end = self.text.find("== %s ==" % chr(ord(initial)+1), begin+1)
    else:
      end = -1

    if self.text[begin:end].find(self.ENTRY_FORMAT % (link_to.name, name)) >= 0:
      return False

    self._insertEntry(initial, name, link_to, begin, end)
    return True


  def removePageLink(self, link_to, author):
    """
      Removes the specified link from the glossary index.
    """
    name = link_to.name[link_to.name.find('/')+1:]
    if self.text.find(self.ENTRY_FORMAT % (link_to.name, name)) == -1:
      return False
    self.text = self.text.replace(self.ENTRY_FORMAT % (link_to.name, name), "")
    return True


  def _insertEntry(self, initial, name, link_to, begin = 0, end = -1):
    """
      Inserts a link entry in the specified region of the index text,
      in alphabetical order.
    """
    text = self.text
    inserted = False
    #============================================================
    # Find the insertion point for the new entry
    #============================================================
    for entry in GlossaryIndexPage.ENTRY_RE.finditer(text[begin:end]):
      if link_to.name < entry.group(1):
	text = text.replace(
	    entry.group(0),
	    "%s%s" % (GlossaryIndexPage.ENTRY_FORMAT % (link_to.name, name), entry.group(0))
	    )
	inserted = True
	break

    #============================================================
    # If the entry wasn't inserted, it's later than all the other
    # entries (or there are no other entries). There is a special
    # case for 'Z' since it ends with a trailing newline that is
    # ignored by the slice into the text.
    #============================================================
    if not inserted:
      if initial == 'Z':
	newline = "\r\n"
      else:
	newline = ""

      text = text.replace(
	  self.text[begin:end],
	  "%s%s%s" % (self.text[begin:end], newline, GlossaryIndexPage.ENTRY_FORMAT % (link_to.name, name))
      )

    self.text = text


  def rebuildAll(self, env, prefix, glossary_index, author = "<author>"):
    """
      Rebuilds the index from all Glossary/* pages in the wiki.
    """
    pre_text = self.text
    index_name = "/".join([prefix, glossary_index])
    for p in wiki.WikiSystem(env).get_pages(prefix):
      if p != index_name:
	self.addPageLink(model.WikiPage(env, p), author)
    #============================================================
    # Avoid nasty 'Page not modified' error
    #============================================================
    if pre_text == self.text: return

    self.save(author, "Rebuilt index", '127.0.0.1')



class GlossaryBuilder(Component):
  """
    Automatically tracks glossary additions to the wiki, which are pages that
    exist under 'Glossary' as a first-level path element. An index page is
    also maintained as Glossary/Index, and a link to this index placed on each
    glossary page. Page deletions are also tracked and removed from the index
    as necessary.

    Example:
    A wiki page is created 'Glossary/Wiki'. A link to the item is
    automatically added to the 'Glossary/Index', which is created if it does
    not exist. A link to the Index is added to the Glossary/Wiki page.

  """
  implements(wiki.IWikiChangeListener, web.IRequestHandler)


  #============================================================
  # IWikiChangeListener methods
  #============================================================

  def wiki_page_added(self, page):
    self.addToIndex(page, "<author>")


  def wiki_page_changed(self, page, version, t, comment, author, ipnr):
    self.addToIndex(page, author)


  def wiki_page_deleted(self, page):
    self.removeFromIndex(page, "<author>")


  def wiki_page_version_deleted(self, page):
    #self.removeFromIndex(page, "<author>")
    # No action.
    pass


  #============================================================
  # IRequestHandler methods
  #============================================================
  anonymous_request = True

  def match_request(self, req):
    url = self.config.get(GLOSSARY_CONFIG_SECTION, 'rebuild_url') or GLOSSARY_REBUILD_URL
    return req.path_info.endswith("/%s" % url)


  def process_request(self, req):
    #============================================================
    # FIXME: <author> should be set from env somehow
    #============================================================
    (prefix, index_author, glossary_index) = self.setupVars("<author>")
    index = findOrCreateIndex(self.env, prefix, glossary_index, index_author)
    index.rebuildAll(self.env, prefix, glossary_index, index_author)
    req.redirect(self.env.href.wiki("%s/%s" % (prefix, glossary_index)))


  #============================================================
  # Class methods
  #============================================================

  def setupVars(self, author):
    prefix = self.config.get(GLOSSARY_CONFIG_SECTION, 'prefix') or GLOSSARY_PREFIX

    glossary_index = self.config.get(GLOSSARY_CONFIG_SECTION, 'index') or GLOSSARY_INDEX
    if not glossary_index: glossary_index = GLOSSARY_INDEX

    index_author = self.config.get(GLOSSARY_CONFIG_SECTION, 'author') or GLOSSARY_AUTHOR
    if index_author == 'author': index_author = author

    return (prefix, index_author, glossary_index)


  def addToIndex(self, page, author):
    """
      Adds a link to the specified page to the glossary index,
      if one is not already present.
    """
    #============================================================
    # XXX: Should we add a link to the index, to the page itself?
    # Seems like a template file header would be a better solution
    # All Glossary pages would then have to use the same template.
    # Feasible?
    #============================================================
    (prefix, index_author, glossary_index) = self.setupVars(author)

    #============================================================
    # If the page is in the glossary, grab the first letter and
    # add it to the index (which is created if it doesn't exist).
    #============================================================
    if not page.name.startswith(prefix): return

    #============================================================
    # Ignore if the page being edited is the index itself
    #============================================================
    if page.name == "/".join([prefix, glossary_index]): return

    index = findOrCreateIndex(self.env, prefix, glossary_index, index_author)
    if (index.addPageLink(page, index_author)):
      index.save(author, "Automatically added link to index", '127.0.0.1')

    #============================================================
    # Potentially add to the page being edited the link to the index
    #============================================================
    link_loc = self.config.get(GLOSSARY_CONFIG_SECTION, "index_link_placement") or GLOSSARY_AUTO_INDEX_LINK_PLACEMENT 
    if link_loc and link_loc.lower() != 'none':
      self.addIndexLink(page, "/".join([prefix, glossary_index]), glossary_index, author, link_loc)


  def addIndexLink(self, page, index_link, index_name, author, location = 'Top'):
    """
      Adds a link to the glossary index to the page being edited.
    """
    #============================================================
    # Nothing to do if a link exists.
    #============================================================
    if page.text.find("[wiki:%s" % index_link) > -1: return


    # TODO: maybe link to the initial of the page itself as fragment identifier?

    if location.lower() == 'top':
      text = "[wiki:%s %s]\r\n\r\n%s" % (index_link, index_name, page.text)
    elif location.lower() == 'bottom':
      text = "%s\r\n\r\n[wiki:%s %s]\r\n" % (page.text, index_link, index_name)
    else:
      return
    page.text = text
    page.save(author, "Automatic insertion of link to index", '127.0.0.1')


  def removeFromIndex(self, page, author):
    """
      Removes the specified page link from the glossary index.
    """
    (prefix, index_author, glossary_index) = self.setupVars(author)
    if not page.name.startswith(prefix): return

    #============================================================
    # Ignore if the page being removed is the index itself
    #============================================================
    if page.name == "/".join([prefix, glossary_index]): return

    index = findOrCreateIndex(self.env, prefix, glossary_index, index_author)
    if index.removePageLink(page, index_author):
      index.save(author, "Automatically removed link from index", '127.0.0.1')


#!/usr/bin/env python

from trac.core import *
import trac.wiki.api as wiki
import trac.wiki.formatter as formatter

class TreeFormatter(object):

  NL = ""

  def __init__(self):
    self.nodes_closed = {}

  def reset(self):
    self.nodes_closed = {}

  def format(self, tree):
    return self.render_tree(tree)


  def format_node(self, node):
    if node.type == Node.TERMINAL:
      return "[ ] %s%s%s" % (node.data, node.comment, self.NL)
    else:
      return "[+] %s%s%s" % (node.data, node.comment, self.NL)


  def format_node_end(self, node):
    return ""


  def render_tree(self, tree, level = 0):
    str = self.format_node(tree)
    for k in tree._kids:
      if k == tree._kids[len(tree._kids) - 1]: self.nodes_closed["%r" % tree] = True
      str += self.render_tree(k, level+1)

    #============================================================
    # Add ancestor rendering in youngest-first mode. This avoids
    # having to calculate the path to this node from the root,
    # so is somewhat faster than a scan over the entire tree.
    #============================================================
    for p in tree.ascend():
      if p == tree.parent:
        str = "+--- %s" % str
      else:
        if self.nodes_closed.has_key("%r" % p):
          str = self.render_closed_ancestor(str)
        else:
          str = self.render_open_ancestor(str)
    if tree.parent: str = self.render_indent(str)

    str += self.format_node_end(tree)
    return str

  def render_closed_ancestor(self, str):
    return "%s%s" % (self.SPACE * 9, str)

  def render_open_ancestor(self, str):
    return "|%s%s" % (self.SPACE * 8, str)

  def render_indent(self, str):
    return "%s%s" % (self.SPACE * 4, str)


class HTMLTreeFormatter(TreeFormatter):
  NL          = "<br/>"
  SPACE       = "&nbsp;"
  EXPAND_STR  = 'V'
  COMPACT_STR = '&gt;'


  def format_node(self, node):
    msg = ""
    if node.comment: msg = " " + node.comment
    if node.type == Node.TERMINAL:
      str = "%s%s%s<div id=\"%s\">" % (node.data, msg, self.NL, node.id)
    else:
      str = \
	"[<a href=\"#\" onclick=\"flip_display('%s', this, '%s', '%s'); return false\">%s</a>] " % (
	node.id, self.EXPAND_STR, self.COMPACT_STR, self.EXPAND_STR) + \
	"%s%s%s<div id=\"%s\">" % (node.data, msg, self.NL, node.id)
    return str

  def format_node_end(self, node):
    return "</div>\n"


class CSSTreeFormatter(HTMLTreeFormatter):

  def render_closed_ancestor(self, str):
    return '<span class="ac">%s</span>' % str

  def render_open_ancestor(self, str):
    return '|<span class="ao">%s</span>' % str

  def render_indent(self, str):
    return '<span class="in">%s</span>' % str

  def css(self):
    return """
<style type="text/css">
  .ao {
    margin-left: 4em;
    border: 1px solid black;
  }
  .ac {
    margin-left: 5em;
    border: 1px solid red;
  }
  .in {
    margin-left: 4em;
    border: 1px solid yellow;
  }
</style>
"""


class TextTreeFormatter(TreeFormatter):
  NL        = "\n"
  SPACE     = " "

  def format_node(self, node):
    if node.type == Node.TERMINAL:
      return "[+] %s%s%s" % (node.data, node.comment, self.NL)
    else:
      return "[+] %s%s%s" % (node.data, node.comment, self.NL)


class Node(object):
  NODEID = 0
  TERMINAL   = 1
  CONTAINER = 2

  def __init__(self, data = None, comment = "", parent = None):
    self._kids   = [] # l-to-r list of sub-nodes (unordered)
    self.data    = data
    self.comment = comment
    self.id      = Node.NODEID
    Node.NODEID  += 1
    self.parent  = None
    self.type    = Node.TERMINAL
    if parent:
      parent.add_node(self)

  def add_node(self, node):
    """ Adds a unique child node. """
    for n in self._kids:
      if node.data == n.data: return n
    self._kids.append(node)
    node.parent = self
    self.type = Node.CONTAINER
    return node


  def add_child(self, data, comment = ""):
    """ Creates and adds a new child node. """
    return self.add_node(Node(data = data, comment = comment))


  def add_path(self, child_path):
    """
      Adds the specified path under the current node, creating any
      intermediate nodes as necessary. Each element in child_path
      may be a string or a 2-tuple consisting of (name, comment).
    """
    while len(child_path) > 0 and not len(child_path[0]): child_path.pop(0)
    if not len(child_path[0]): return None

    #============================================================
    # Attempt to find the node at which to insert the child_path,
    # by examining the direct children in order.
    #============================================================
    top = None
    elem_to_add = child_path[0]
    if type(elem_to_add) == tuple:
      (elem_name, msg) = elem_to_add[0:1]
    else:
      (elem_name, msg) = (elem_to_add, "")

    for k in self._kids:
      if k.data == elem_name: top = k

    #============================================================
    # If the top node wasn't found, add it, then the remainder of
    # the path.
    #============================================================
    if not top:
      top = self.add_node(Node(data = elem_name, comment = msg))
    if len(child_path) > 1:
      top = top.add_path(child_path[1:])
    return top


  def traverse(self):
    """ Walk a node and all of its subnodes in depth-first order. """
    yield self
    for k in self._kids:
      for kk in k.traverse():
        yield kk


  def ascend(self):
    """ Walk up the tree from a node. """
    node = self.parent
    while node:
      yield node
      node = node.parent


  def find_child(self, data):
    """
      Attempts to find a node containing the provided data below the current node.
    """
    for c in self.traverse():
      if c == self: continue
      if c.data == data: return c
    return None

##  No need for this yet..
##  def match_children(self, data):
##    """ Returns a generator of all matching children. """
##    for c in self.traverse():
##      if c.data == data: yield c

  def __str__(self):
    return TextTreeFormatter().format(self)


class TreeView(Component):
  """ Models a tree of items provided with special trac syntax. """

  implements(wiki.IWikiSyntaxProvider)

  def __init__(self):
    self.root  = None
    self.delim = None


  def render_js(self):
    return """
<script type="text/javascript">
function flip_display(id, trigger, expand_str, compact_str)
{
  elem = document.getElementById(id);
  style = elem.style;
  if (style.display) {
    if (style.display == 'none') {
      style.display = 'block';
      trigger.innerHTML = expand_str;
    } else {
      style.display = 'none';
      trigger.innerHTML = compact_str;
    }
  } else {
    style.display = "none";
    trigger.innerHTML = compact_str;
  }
  return false;
}
</script>
"""


  def _modify_tree(self, frm, ns, match):
    text = match.group(0)

    if ns == '--':
      if not self.root: return ns
      #============================================================
      # Reached the end of this tree. If the root has only a single
      # child, throw the root away.
      # Close the tree & render, then reset.
      #============================================================
      if self.root.data == self.delim and len(self.root._kids) == 1:
        self.root = self.root._kids[0]
        self.root.parent = None
      tree = self.render_js()                   + \
        '<div style="font-family: monospace;">' + \
        HTMLTreeFormatter().format(self.root)   + \
        "</div>"
      self.close_tree()
      return tree

    self.create_nodes(text[2:])

    #============================================================
    # Return empty string so nothing gets rendered.. yet.
    #============================================================
    return ""


  def create_nodes(self, text):
    #============================================================
    # Separate out any comment - this is done prior to splitting
    # on the delimiter to allow delimiter tokens in comments.
    # The comment will be applied to the last-added node.
    #============================================================
    if text.find(' ') > -1:
      (name, comment) = text.split(' ', 1)
    else:
      (name, comment) = (text, '')

    final_node_type = Node.TERMINAL

    if not self.root:
      self.delim = name[0]
      name = name[1:]
      if self.delim.isspace():
	raise NotImplementedError("Can't use whitespace as node delimiter")
      #============================================================
      # If the last character is the node delimiter, the final node
      # type will be set to 'Container'
      #============================================================
      if name[-1] == self.delim:
        final_node_type = Node.CONTAINER
        name = name[:-1]
      elems = name.split(self.delim)
      self.root = Node(self.delim)
      child = self.root

    else:
      #============================================================
      # If the last character is the node delimiter, the final node
      # type will be set to 'Container'
      #============================================================
      if name[-1] == self.delim:
        final_node_type = Node.CONTAINER
        name = name[:-1]

      if name[0] == self.delim:
	#============================================================
	# If first character is delimiter, start from the absolute root.
	#============================================================
	name = name[1:]
	child = self.root
	elems = name.split(self.delim)

      else:
	#============================================================
	# Otherwise find the first child, and add the path.
	# If the child wasn't found, add path elements to the root.
	#============================================================
	elems = name.split(self.delim)
	top = elems.pop(0)
	if top: child = self.root.find_child(top) or self.root.add_child(top)

    nodes = self.add_nodelist(child, elems, final_node_type)
    nodes[-1].comment = comment


  def add_nodelist(self, root, nodelist, leaftype = Node.TERMINAL):
    """
      Adds the specified nodelist to root, optionally setting
      the leaf node's type.
    """
    nodes = []
    for n in nodelist[:-1]:
      root = root.add_child(n)
      nodes.append(root)
    root = root.add_child(nodelist[-1])
    root.type = leaftype
    nodes.append(root)
    return nodes

  
  def close_tree(self):
    """ Ends node processing """
    self.root = None
    self.delim  = None

  #============================================================
  # IWikiSyntaxProvider methods
  #============================================================

  def get_wiki_syntax(self):
    yield ('^\+-([^\n]+)|--', lambda frm, ns, match: self._modify_tree(frm, ns, match))


  def get_link_resolvers(self):
    yield (None, None)


"""
Ideas/ TODO:

 1. Config options for expand/ compact characters, or images to use instead
 1. Config options for 'compact X subtrees by default' (yeech!)
 1. Config options for syntax characters

"""


#============================================================
# Testing code - only tests tree/ render functions, not
# trac text parsing -> node creation.
#============================================================

def equal(expected, got, msg = None):
  if expected == got:
    print "ok"
  else:
    print "not ok: expected \n%s, got \n%s" % (expected, got)


def test():
  test_simple_1()
  test_intermediate_node_creation()
  test_node_selection()
  test_node_disambiguation()
  test_reroot()
  test_dupe_node()


def test_dupe_node():
  root = Node(data = 'top')
  c1 = root.add_node(Node(data = '1stChild'))
  c2 = root.add_node(Node(data = '1stChild'))
  equal(repr(c1), repr(c2))
  c1_1 = c1.add_node(Node(data = '1stGrandchild'))
  c1_2 = c1.add_child('1stGrandchild')
  equal(repr(c1_1), repr(c1_2))


def test_node_selection():
  root = Node(data = "org")
  tbm = root.add_child("example")
  root.add_path(["example", "www"])
  root.add_path("example.mail".split('.'))
  root.add_path("example.mail".split('.')) # Same node is silently ignored.
  tbm.add_path("ns".split('.'))
  str = TextTreeFormatter().format(root)
  equal("""[+] org
    +--- [+] example
             +--- [+] www
             +--- [+] mail
             +--- [+] ns
""", str)


def test_node_disambiguation():
  root = Node(data = "A")
  root.add_path(["A", "A", "B"])
  root.add_path(["A", "B", "C"]) # Will use first 'A' (under root A).
                                 # Use just ["B"] to add under root directly. 
  str = TextTreeFormatter().format(root)
  equal("""[+] A
    +--- [+] A
             +--- [+] A
             |        +--- [+] B
             +--- [+] B
                      +--- [+] C
""", str)
  root.add_path(["B"])
  str = TextTreeFormatter().format(root)
  equal("""[+] A
    +--- [+] A
    |        +--- [+] A
    |        |        +--- [+] B
    |        +--- [+] B
    |                 +--- [+] C
    +--- [+] B
""", str)



def test_intermediate_node_creation():
  c1 = Node(data = 'c1')
  c1_1_1_1 = c1.add_path(["c1_1", "c1_1_1", "c1_1_1_1"])
  str = TextTreeFormatter().format(c1)
  equal("""[+] c1
    +--- [+] c1_1
             +--- [+] c1_1_1
                      +--- [+] c1_1_1_1
""", str)


def test_simple_1():
  root = Node(data = 'top')
  root.add_path("foo".split(":"))
  root.add_path("bar".split(":"))
  str = TextTreeFormatter().format(root);
  equal("""[+] top
    +--- [+] foo
    +--- [+] bar
""", str)


def test_reroot():
  orig_root = Node(data = "original_root")
  orig_root.add_path(["child1"])
  new_root = Node(data = "new_root")
  new_root.add_node(orig_root)
  str = TextTreeFormatter().format(new_root)
  equal("""[+] new_root
    +--- [+] original_root
             +--- [+] child1
""", str)


if __name__ == '__main__':
  test()

from trac.wiki.macros import WikiMacroBase
import shlex

revison = "$Rev$"
url = "$URL$"

class InsertElementMacro(WikiMacroBase):
    """
    This macro allows you to insert HTML elements with a class or id without having to use a HTML preprocessor.

    Author: Marc E. <santusmarc@users.sourceforge.net>
    License: Copyright 2007 Marc, E. Trac license. http://trac.edgewall.org/wiki/TracLicense
    URL: http://trac-hacks.org/wiki/InsertElementMacro

    Usage:
    {{{
      [[InsertElement(element, property, value, content)]]
    }}}

    Where: 
     * '''element'''
      Name of an HTML element like div or p
     * '''property'''
      Name of the HTML property such as class or id
     * '''value'''
      The value of the property
     * '''content'''
      The '''quoted''' string for the content of the element

    Examples:
    {{{
      [[InsertElement(div, class, quote, "This is a very nice quote")]]
      [[InsertElement(p, id, unique, "This is a unique paragraph, commas in the last argument don't interfere")]]
      [[InsertElement(a, id, uniquea, "You can represent actual quotes by using &quot;entities&quot;")]]
      [[InsertElement(pre, id, uniqueb, 'Or you can change the type of "outer quote"')]]
    }}}

    Result:
    {{{
        <div class="quote">This is a very nice quote</div>
        <p id="unique">This is a unique paragraph, commas in the last argument don't interfere</p>
        <a id="uniquea>You can represent actual quotes by using &quot;entities&quot;</a>
        <pre id="uniqueb">Or you can change the type of "outer quote"</pre>
    }}}
    """

    def expand_macro(self, formatter, name, args):
        args = shlex.split(str(args))
        tag = args[0][:-1]
        selector = args[1][:-1]
        selector_name = args[2][:-1]
        content = args[3]

        return '<%s %s="%s">%s</%s>' % (tag, selector, selector_name, content, tag)

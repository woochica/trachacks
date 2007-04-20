= ExtLinkRewriter Plugin =

  bellbind@gmail.com

== goal ==

Rewrite external link format, for example, to hide referers for private sites.

== install ==
1. make egg and then copy the egg into trac plugins dir.
{{{
$ python setup.py bdist_egg
$ cp dist/*.egg /where/to/trac/plugins/
}}}

2. edit conf/trac.ini
{{{
[components]
ExtLinkRewriter.* = enabled
}}}

3a. use rediretor
copy redirector/rediretor.html at accessible point.
{{{
$ cp redirector/rediretor.html /var/www/
}}}

edit trac.ini
{{{
[extlinkrewriter]
format = /redrector.html?%s
namespaces = http,https,ftp
target = _blank
}}}

3b. use social bookmark site
edit trac.ini
{{{
[extlinkrewriter]
format = http://del.icio.us/url?url=%s
namespaces = http,https
}}}


== site ==
 * http://www.trac-hacks.org/wiki/ExtLinkRewriterPlugin

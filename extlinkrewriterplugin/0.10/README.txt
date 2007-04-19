= ExtLinkRewriter Plugin =

  bellbind@gmail.com

== goal ==

Rewrite external link format, for example, to hide referers for private sites.

== install ==
1. copy redirector/rediretor.html at accessible point.
{{{
$ cp redirector/rediretor.html /var/www/
}}}

2. make egg and then copy the egg into trac plugins dir.
{{{
$ python setup.py bdist_egg
$ cp dist/*.egg /where/to/trac/plugins/
}}}

3. edit conf/trac.ini
{{{
[components]
ExtLinkRewriter.* = enabled
}}}

and options
{{{
[extlinkrewriter]
format = /redrector.html?%s
namespaces = http,https,ftp
target = _blank
}}}

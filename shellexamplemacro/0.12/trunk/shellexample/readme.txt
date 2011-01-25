== Shell Example ==
This plugin was originally developed by mOo moolighttpd@gmail.com
located at http://xcache.lighttpd.net/wiki/ShellExample. This plugin is now
maintained by Nathaniel Madura nmadura@umich.edu

This plugin has only been tested on Trac 0.12, but may work with earlier versions.

=== Installation ===
You can install this software as normal Trac plugin.

 1. Uninstall ShellExample wiki processor if you have installed before.

 2. Change to the directory containning setup.py.

 3. If you want to install this plugin globally, that will install this plugin to the python path:
  * python setup.py install

 4. If you want to install this plugin to trac instance only:
  * python setup.py bdist_egg
  * copy the generated egg file to the trac instance's plugin directory
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 5. Config trac.ini:
  {{{
[components]
shellexample.* = enabled
}}}

=== Details ===
This is a [wiki:WikiProcessors WikiProcessor] so it is used with the standard #! notation. This processor injects css code into Trac, so you should get formatted output by default. Any tagged code is inside a span element, and the following classes are used:
 * se-input
 * se-input-userreplacement
 * se-input-string
 * se-input-continuation
 * se-input-option
 * se-input-delayed
 * se-prompt
 * se-prompt-start
 * se-prompt-user
 * se-prompt-userhostseparator
 * se-prompt-host
 * se-prompt-path
 * se-prompt-end
 * se-root
 * se-unprivileged
 * se-note
 * se-output
 * se-output-snipped

=== Usage ===

 1. Standard shebang (#!) notation is used
 {{{

#!ShellExample
}}}
 1. as is typical for a shell a $ or # (root) is used to indicate the start of user input, the line need not start with that character. User input is tagged (in css) separately from the $ to indicate its difference.
 {{{

#!ShellExample
# foo
$ foo
}}}
 {{{
#!ShellExample
# foo
$ foo
}}}
 1. Hopefully many of the conventional shell identifiers have been accounted for.
 {{{

#!ShellExample
baruser$ foo
{user@foo ~/path/to}$ foo
[otheruser@foo]$ foo
}}}
 {{{
#!ShellExample
baruser$ foo
{user@foo ~/path/to}$ foo
[otheruser@foo]$ foo
}}}
 1. Parenthesis are used to indicate a note
 {{{
{{{
#!ShellExample
(become root and install)
~ $ su
~ # make install
}}}
}}}
 {{{
#!ShellExample
(become root and install)
~ $ su
~ # make install
}}}
 1. Command line switches/options are also recognized and highlighted differently, as are strings that are in the input
 {{{
{{{
#!ShellExample
{user@foo ~/path/to}$ foo -v --hello --hello="something"
}}}
}}}
 {{{
#!ShellExample
{user@foo ~/path/to}$ foo -v --hello --hello="something"
}}}
 1. Shell continuation is also recognized, just make sure there is no white space after the backslash
 {{{
{{{
#!ShellExample
{user@foo ~/path/to}$ foo \
--some \
--multiline \ 
--input='something'
}}}
}}}
 {{{
#!ShellExample
{user@foo ~/path/to}$ foo \
--some \
--multiline \
--input='something'
}}}
 1. If the user has to input something soft braces can be used to bring attention to it
 {{{

#!ShellExample
{user@foo ~/path/to}$ foo --user {username}
}}}
 {{{
#!ShellExample
{user@foo ~/path/to}$ foo --user {username}
}}}
 1. Example output can be included, and will be highlighted differently
 {{{
{{{
#!ShellExample
{user@foo ~/path/to}$ cat lorem.txt
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim 
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate 
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat 
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum.
}}}
}}}
 {{{
#!ShellExample
{user@foo ~/path/to}$ cat lorem.txt
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim 
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate 
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat 
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum.
}}}
 1. Long sample output can be trimmed and annotated with $$---, if a string is included after the tag, that string is used otherwise <Output Snipped> will appear
 {{{
{{{
#!ShellExample
{user@foo ~/path/to}$ cat lorem.txt
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim 
$$--- Unnecessary text deleted
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum.
}}}
}}}
 {{{
#!ShellExample
{user@foo ~/path/to}$ cat lorem.txt
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim 
$$--- Unnecessary text deleted
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum.
}}}
 1. Input can appear in the output by using $$ at the start of the line.
 {{{
{{{
#!ShellExample
(full example showing how to use openssl to connect to a pops mail server)
[foo@bar ~]$ openssl s_client -connect mail.foo.com:995
CONNECTED(00000003)
depth=0 /C=US/ST=Nowhere/O=Foo/OU=bar/CN=mail.foo.com
$$---
---
+OK Dovecot ready. <1c32.1a611.4c4859c2.BEuUvAEtnt0du+msvFig0w==@mail.foo.com>
$$ user {username}
+OK
$$ pass {password}
+OK Logged in.
$$ stat
+OK 509 15659197
$$ quit
+OK Logging out.
closed
}}}
}}}
 {{{
#!ShellExample
(full example showing how to use openssl to connect to a pops mail server)
[foo@bar ~]$ openssl s_client -connect mail.foo.com:995
CONNECTED(00000003)
depth=0 /C=US/ST=Nowhere/O=Foo/OU=bar/CN=mail.foo.com
$$---
---
+OK Dovecot ready. <1c32.1a611.4c4859c2.BEuUvAEtnt0du+msvFig0w==@mail.foo.com>
$$ user {username}
+OK
$$ pass {password}
+OK Logged in.
$$ stat
+OK 509 15659197
$$ quit
+OK Logging out.
closed
}}}

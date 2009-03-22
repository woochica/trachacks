= TracEditorGuide =

Editor's Guide navigation item plugin for Trac.

Plugin adds extra navigation item to '''metanav'''. This is a link to Editor's Guide, which
is visible only for users who have permission to edit wiki pages.

== Installation ==
 1. Run: python setup.py compile_catalog -f ('''only for Trac 0.12''')
 2. Run: python setup.py bdist_egg
 3. If necessary create a folder called "plugins" in your Trac environment.
 4. Copy the .egg file from the dist folder created by step 1 into the "plugins"
    directory of your Trac environment.

== Configuration ==
If necessary, edit trac.ini section as in the example below. By default
item links to page !EditorGuide

{{{
[editorguide]
page = MyEditorGuide
}}}
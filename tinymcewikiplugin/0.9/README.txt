TinyMce Wiki Plugin

Description 

 This plugin allows users to edit wiki with the TinyMCE.TinyMCE is a platform independent web based Javascript HTML WYSIWYG editor control released as Open Source under LGPL by Moxiecode Systems AB.

 In this plugin, you can also use the Traclink, the Macro, the Links and the Processer.

Caution 

 The data which it retains is not wiki grammar, is the individual type which includes the Traclink and the Macro et cetera to the HTML. Considerably it becomes difficult to edit the data which it retains with the wiki editor of default.

Installation 

1. Download and put TinyMCE

    You must download the TinyMCE from http://tinymce.moxiecode.com/ . And you must put 'tinymce' directory (not 'tiny_mce') into share/trac/htdocs.

2. put 'tinymce_trac.css'

    copy 'tinymce_trac.css' in this plugin to tinymce folder.

3. Disable Wiki Module

    This plugin replaces the default wiki module. You must adding the following options to trac.ini:

[components]
trac.wiki.web_ui.WikiModule= disabled

    If you have not modified default_handler, You must adding the following options too.

[trac]
default_handler = TinyMceWikiPlugin

4. Put this plug-in

    Put tinymcewiki-0.1-py2.3.egg to Your TracEnv/plugins

To customize the TinyMCE 

 The TinyMCE-Plugin reads the tinymceconf.cs which is placed on the templates folder of the TracEnv. Reading the document of the TinyMCE, please rewrite this file.

To rewrite to the language of your country 

 The TinyMCE-Plugin reads the tinymcewiki.cs which is placed on the templates folder of the TracEnv. Please rewrite this file.
Bugs/Feature Requests 

Author: hirobe

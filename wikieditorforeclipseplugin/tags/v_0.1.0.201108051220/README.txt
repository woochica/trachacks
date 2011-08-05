== Description ==

WikiEditor4Eclipse is a new plug-in providing Trac Wiki editing capabilities to Eclipse IDE.
This plugin is hosted at : http://trac-hacks.org/wiki/WikiEditorForEclipsePlugin

Features:

	* Trac Wiki Servers explorer
	* Eclipse Wiki Editor: currently, it borrows the editor from the original EclipseTracPlugin plugin.
	* Wiki Page managment: Creation, edition and page deletion.
	* Concurrent edition management:
		- Prevents overwriting other users changes when a concurrent edit happens.
		- Helps merge contents when a concurrent edit happens. 

== Instalation ==

!WikiEditor4Eclipse comprises a Wiki Editor as an [http://eclipse.org Eclipse] plugin that comunicates with Trac wiki server through the XmlRpcPlugin. It requires the following software to be installed:

=== Server ===

	* XmlRpcPlugin: !WikiEditor4Eclipse requires XmlRpcPlugin to be installed and enabled on the server

	* [download:eclipsetracplugin/tracrpcext/0.10 TracRpcExt] (optional): !WikiEditor4Eclipse reuses !TracRpcExt plugin from EclipseTracPlugin to provide a ''page history'' view. This dependency is optional as the editor can work without it, but if its not installed and enabled you will miss page history functionality.  

=== Client ===

	* Add  [http://trac-hacks.org/svn/wikieditorforeclipseplugin/trunk/releases/update-site] to Eclipse Update Manager (Help -> Software Upates -> Available Software -> Add Site). This plugin requires Java Runtime version 1.5 or higher and Eclipse SDK 3.2 or higher (it was tested successfully on Eclipse SDK 3.4.2).


=== Building from Source ===

In order to build !WikiEditor4Eclipse you will need the following software:

	* Subversion client
	* Java JDK >= 1.5
	* [http://docs.codehaus.org/display/M2ECLIPSE/Tycho+builds Tycho] maven plugin (tested with version 0.3.0-DEV-1819)
	* Eclipse SDK >= 3.2 (tested with version 3.4.2)
	
{{{
#!sh
svn co http://trac-hacks.org/svn/wikieditorforeclipseplugin/trunk/source/ WikiEditor4Eclipse
cd WikiEditor4Eclipse
/opt/tycho-distribution-0.3.0-DEV-1819/bin/mvn \
 -Dtycho.targetPlatform=/opt/eclipse/eclipse-SDK-3.4.2 \
 clean install -Dmaven.test.skip
}}}

This will create a local eclipse update site at ''!TracWikiEditor?4Eclipse/source/eclipse/org.trachacks.wikieditor.eclipse.site/target/site'' you can point Eclipse Update Manager to. 
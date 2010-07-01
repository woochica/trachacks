Google Analytics Integration
============================

Previously known as ` (Trac) Google Analytics Plugin`_, this plugin will 
enable your Trac environment to be logged by Google Analytics.

It ads the necessary javascript code to log your environment, plus, it also
logs the downloads of regular filenames which end with a specific extension;
these extensions are defined by you; and also external links.

Download and Install
--------------------

The easiest way to install is using EasyInstall_:

.. sourcecode:: sh

  sudo easy_install GoogleAnalyticsIntegration


Then, to enable the plugin add to the ``[components]`` section in your
``trac.ini``:

.. sourcecode:: ini

  [components]
  googleanalytics.* = enabled


Configuration
-------------

The necessary configuration is:
 * **UID**: Google Analytics' UID. The UID is needed for Google Analytics to
   log your website stats. Your UID can be found by looking in the JavaScript
   Google Analytics gives you to put on your page. Look for your UID in
   between the javascript::

     var pageTracker = _gat._getTracker("UA-111111-11");

   In this example you would put **UA-11111-1** in the UID box.

There are other, more advanced configuration options:
 * **admin_logging**: Disabling this option will prevent all logged in
   ``TRAC_ADMIN``'s from showing up on your Google Analytics reports.
 * **authenticated_logging**: Disabling this option will prevent all
   authenticated users from showing up on your Google Analytics reports.
 * **outbound_link_tracking**: Disabling this option will turn off the
   tracking of outbound links.
   It's recommended not to disable this option unless you're a privacy
   advocate (now why would you be using Google Analytics in the first place?)
   or it's causing some kind of weird issue.
 * **google_external_path**: This will be the path shown on Google Analytics
   regarding external links. Consider the following link::

     <a href="http://trac.edgewall.org/">Trac</a>

   The above link will be shown as::

      /external/trac.edgewall.org/

   This way you will be able to track outgoing links. Outbound link tracking
   must be enabled for external links to be tracked.
 * **extensions**: Enter any extensions of files you would like to be tracked
   as a download. For example to track all MP3s and PDFs enter **mp3,pdf**.
   Outbound link tracking must be enabled for downloads to be tracked.
 * **tracking_domain_name**: If you're tracking multiple subdomains with the
   same Google Analytics profile, like what's talked about here_, enter your
   main domain here. For more info, please visit the previous link.


Bugs and/or New Features
------------------------

Please submit bugs of new features to::

  http://trac-hacks.org/wiki/GoogleAnalyticsIntegration


Source Code
-----------

If you wish to be on the bleeding edge and get the latest available code:

.. sourcecode:: sh

  svn co http://trac-hacks.org/svn/GoogleAnalyticsIntegration

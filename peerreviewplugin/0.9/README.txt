TEAM5                                      
A Distributed Peer-Review Plug-in for TRAC Project Management System
README

===================
License Information
===================
This software is licensed as described in the file COPYING.txt, which 
you should have received as part of this distribution. 

============
Installation
============
Installation instructions for a Trac plugin can be located at 
Edgewall Software <http://projects.edgewall.com/trac/wiki/TracPlugins>.

======================================
Configuring Trac's main navigation bar
======================================
By default, the navigation button for the Peer Review button will appear
on the far right of the main navigation bar in Trac.  It is only visible 
when a valid user logs into the system.  To change this option, locate
and modify the following line in the trac.ini file.  It may be commented
out, so first uncomment the line.

mainnav = wiki,timeline,roadmap,browser,peerReviewMain,tickets,newticket,search


The above example places the Peer Review button (called codereview) between
the browser and tickets buttons.  You can rearrange these in any order for
your desired effect.

======================
How to add user rights
======================
User priveledges can be set using Trac's built-in administrative program:
trac-admin.  The possible user priveledges are as follows:

CODE_REVIEW_DEV : Individuals with this access level will be able to view, 
create, search, and perform code reviews.

CODE_REVIEW_MGR : This access level allows users to modify the status of a
code review and change the plugin configuration options, along with all the
priveledges present in CODE_REVIEW_DEV.

Please refer to trac-admin help utility for information on how to set
user priveledges.

*Note: Granting the aforementioned priviledges to anonymous exclusively, without
specifying other specific users, will result in a situation where our plugin cannot correctly
 identify users. This method of operation is not supported.

=======
Authors
=======
The original purpose of the project was for a 2005-2006 senior project at
Rose-Hulman Institute of Technology.  The project supervisor was Mark Ardis, and
the project client was William Nagel.  The team members consisted of:

Brandon Cannaday
Gabriel Golcher
Michael Kuehl
Anthony Panozzo
Adam Westhusing

===================
Contact information
===================
Website - http://tracreview.sourceforge.net
Email   - tracteam5@users.sourceforge.net

= ImageTracPlugin =

The ImageTracPlugin allows images to be attached to Trac tickets and displayed.

== Components ==

Several 
[http://trac.edgewall.org/wiki/TracDev/ComponentArchitecture components]
are included in the ImageTrac plugin:

 * [#ImageTrac ImageTrac]
 * [#DefaultTicketImage DefaultTicketImage]
 * [#Galleria Galleria]
 * [#ImageFormFilter ImageFormFilter]
 * [#SidebarImage SidebarImage]
 * [#TicketImageHandler TicketImageHandler]


=== !ImageTrac ===

!ImageTrac is the core of the ImageTracPlugin.  This plugin processes
 uploaded attachments and, if they are images, will create images of
 the appropriate size as dictated by the `[ticket-image]` section of
 the [http://trac.edgewall.org/wiki/TracIni trac.ini] configuration.

Two sizes are included by default, thumbnails and a default size, but
an arbitrary number of sizes can be used.  Configuration is given for
the default case as follows

{{{
[ticket-image]
size.thumbnail = 32x32
size.default = 488x
}}}

This specifies a thumbnail of 32 by 32 pixels and a default size of
488 pixels in width with a height taken from the aspect ratio of the
uploaded image.  Currently, images are not scaled up.  Scaling is done
with the 
[http://www.pythonware.com/products/pil/ Python Imaging Library] and a
front-end function packaged in 
[http://pypi.python.org/pypi/cropresize cropresize].

!ImageTrac can also enforce image uploading on ticket creation and
 includes the ticket images in the data passed to the `ticket.html`
 template. 


=== !DefaultTicketImage ===

The !DefaultTicketImage component allows the setting of a default
image for a ticket.  It maintains a database table, `default_image`,
which stores which image is the default


=== Galleria ===

The Galleria component adds the 
[http://devkick.com/lab/galleria/ galleria] javascript image gallery
and accompanying CSS to allow the display of images in a gallery
format.


=== !ImageFormFilter ===

The !ImageFormFilter component adds a form on the ticket page that
allows uploading of an image on ticket creation or ticket editing.
Images so uploaded should become the default image (NOTE: there is
currently a bug whereby this is not the case).


=== !SidebarImage ===

The !SidebarImage component displays the images in an unordered list
in the ticket sidebar using the
[http://trac-hacks.org/wiki/TicketSidebarProviderPlugin
TicketSidebarProviderPlugin].  
(NOTE:  currently, thumbnails are displayed full size.  This is
bad. See http://trac-hacks.org/ticket/5657)


=== !TicketImageHandler ===

The !TicketImageHandler component serves the images at
`/ticket/<ticket id>/image/<size>`.  For example, the thumbnail of
ticket 67 would be displayed at `/ticket/67/image/thumbnail`.


== Usage ==

It is recommended that you enable all of the components of the
ImageTracPlugin.

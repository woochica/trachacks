PHP Contact Form with Spam Protection Installation Instructions
---------------------------------------------------------------

Open contact-form.php and edit the values after this section:

/*******************************************************************************
 *	Script configuration - Refer README.txt
*******************************************************************************/

/* Email address where the messages should be delivered */
$to = 'youremail@email.com';

/* From email address, in case your server prohibits sending emails from addresses other than those of your 
own domain (e.g. email@yourdomain.com). If this is used then all email messages from your contact form will appear 
from this address instead of actual sender. */
$from = '';

/* This will be appended to the subject of contact form message */
$subject_prefix = 'My Website Contact';

The form can be run as it is just by editing the above three values.

To modify form background, border, etc. modify the corresponding values in the file.

For hex color codes (form background, border, etc.), visit:
http://www.2createawebsite.com/build/hex-colors.html

Upload all 6 files to web server either to the root or to any folder. That's it!

To access the form, just enter the path to contact-form.php in your web browser:

http://www.yourwebsite.com/contact-form.php (if you have uploaded all files to the root)

http://www.yourwebsite.com/form/contact-form.php (if you have uploaded all files to a folder 'form' under root)

You can also rename contact-form.php to any name. But do not forget to keep the .php extension.

To customize the form according to the structure of your site, just enter header and footer information in 
form-header.php and form-footer.php

Note: If you know little PHP then you can tinker with securimage.php to change the 
looks of the image verification code to match your site :)

That's it! If you need any help, you can contact me through:
http://www.easyphpcontactform.com/contact.php

If you liked the script, please take some time to rate this script at:
http://php.resourceindex.com/detail/08023.html

Cheers!

Vishal P. Rao
http://www.easyphpcontactform.com/

Note: The only way you can use the form free of charge is by keeping the
attribution link intact. If not on the contact page, then on any accessible
page of your website.
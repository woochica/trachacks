package mm.eclipse.trac.editors;

import mm.eclipse.trac.Log;
import mm.eclipse.trac.models.WikiPage;

import org.eclipse.swt.SWT;
import org.eclipse.swt.browser.Browser;
import org.eclipse.swt.widgets.Composite;

public class WikiPreview
{
    private Browser             browser  = null;
    
    private final static String template = "<?xml version=\"1.0\" encoding=\"utf-8\"?> "
                                                 + "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\"> "
                                                 + "<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en\" xml:lang=\"en\"> "
                                                 + "  <head> "
                                                 + "    <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" /> "
                                                 + "    <style type=\"text/css\"> "
                                                 + "</style> "
                                                 + "<link rel=\"stylesheet\" href=\"{server.url}chrome/common/css/trac.css\" type=\"text/css\" /> "
                                                 + "<link rel=\"stylesheet\" href=\"{server.url}chrome/common/css/wiki.css\" type=\"text/css\" /> "
                                                 + "</head> "
                                                 + "<body> "
                                                 + "<div id=\"main\"> "
                                                 + "<div id=\"content\" class=\"wiki\"> "
                                                 + "<div class=\"wikipage\"> "
                                                 + "<div id=\"searchable\"> "
                                                 + "{page.content}"
                                                 + "</div> "
                                                 + "</div> "
                                                 + "</div> "
                                                 + "<div id=\"footer\"> "
                                                 + "<hr /> "
                                                 + "</div> "
                                                 + "</div> "
                                                 + "</body> "
                                                 + "</html> ";
    
    /**
     * Create the browser component by initialising the browser in the frame.
     */
    public WikiPreview( Composite frame )
    {
        browser = new Browser( frame, SWT.NONE );
    }
    
    /**
     * Disposes the internal browser widget.
     */
    public void dispose()
    {
        browser.dispose();
        browser = null;
    }
    
    public void showContent( WikiPage page, String wikiSource )
    {
        try
        {
            String htmlContent = page.getServer().getWiki().wikiToHtml(
                    wikiSource );
            
            String content;
            String serverUrl = page.getServer().getUrl().toString();
            if ( !serverUrl.endsWith( "/" ) )
                serverUrl += "/";
            
            content = template.replace( "{server.url}", serverUrl );
            content = content.replace( "{page.content}", htmlContent );
            
            browser.setText( content );
            
        } catch ( Throwable t )
        {
            Log.error( "Error in getting the HTML preview.",
                            new Exception( t ) );
        }
    }
    
    /**
     * Delegates focussing this view to the browser, so that it can handle
     * mouse-clicks etc.
     */
    public void setFocus()
    {
        browser.setFocus();
    }
}

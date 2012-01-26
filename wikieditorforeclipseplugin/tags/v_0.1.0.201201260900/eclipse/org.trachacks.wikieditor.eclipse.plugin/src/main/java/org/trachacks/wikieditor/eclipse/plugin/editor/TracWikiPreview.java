/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.net.URL;

import org.eclipse.jface.text.Region;
import org.eclipse.jface.text.hyperlink.URLHyperlink;
import org.eclipse.swt.SWT;
import org.eclipse.swt.browser.Browser;
import org.eclipse.swt.browser.LocationEvent;
import org.eclipse.swt.browser.LocationListener;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.PlatformUI;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class TracWikiPreview {

	private Browser browser;

	
	
	public TracWikiPreview(Composite parent) {
		super();
		browser = createPreviewBrowser(parent);
	}



	public Browser getBrowser() {
		return browser;
	}
	
	private Browser createPreviewBrowser(Composite parent) {
		Browser browser = new Browser(parent, SWT.NONE);
		// bug 260479: open hyperlinks in a browser
		browser.addLocationListener(new LocationListener() {
			public void changed(LocationEvent event) {
				event.doit = false;
			}

			public void changing(LocationEvent event) {
				// if it looks like an absolute URL
				if (event.location.matches("([a-zA-Z]{3,8})://?.*")) { //$NON-NLS-1$

					// workaround for browser problem (bug 262043)
					int idxOfSlashHash = event.location.indexOf("/#"); //$NON-NLS-1$
					if (idxOfSlashHash != -1) {
						// allow javascript-based scrolling to work
						if (!event.location.startsWith("file:///#")) { //$NON-NLS-1$
							event.doit = false;
						}
						return;
					}
					// workaround end

					event.doit = false;
					try {
						PlatformUI.getWorkbench().getBrowserSupport().createBrowser("org.eclipse.ui.browser") //$NON-NLS-1$
								.openURL(new URL(event.location));
					} catch (Exception e) {
						new URLHyperlink(new Region(0, 1), event.location).open();
					}
				}
			}
		});
		return browser;
	}

	private final static String template = "<?xml version=\"1.0\" encoding=\"utf-8\"?> "
		+ "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\"> "
		+ "<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en\" xml:lang=\"en\"> "
		+ "  <head> "
		+ "    <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" /> "
		+ "    <style type=\"text/css\"> "
		+ "</style> "
		+ "<link rel=\"stylesheet\" href=\"{server.url}/chrome/common/css/trac.css\" type=\"text/css\" /> "
		+ "<link rel=\"stylesheet\" href=\"{server.url}/chrome/common/css/wiki.css\" type=\"text/css\" /> "
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
		+ "</body> " + "</html> ";
	
	public void showPreview(Page page, String wikiSource) {
		String previewContent = null;
		if(page.getServer().isConnected()) {
			String wikiToHtml = page.wikiToHtml(wikiSource);
			previewContent = template.replace("{server.url}", page.getServer().getServerDetails().getUrl().toString());
			previewContent = previewContent.replace("{page.content}", wikiToHtml);
		}
		else {
			previewContent = "Server is not connected";
		}
		
		browser.setText(previewContent);
	}
	
	
}

package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.swt.SWT;
import org.eclipse.swt.browser.Browser;
import org.eclipse.swt.widgets.Composite;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

public class WikiPreview {
	private Browser browser = null;

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

	/**
	 * Create the browser component by initialising the browser in the frame.
	 */
	public WikiPreview(Composite frame) {
		browser = new Browser(frame, SWT.NONE);
	}

	/**
	 * Disposes the internal browser widget.
	 */
	public void dispose() {
		browser.dispose();
		browser = null;
	}

	public void showContent(Page page, String wikiSource) {
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

	/**
	 * Delegates focussing this view to the browser, so that it can handle
	 * mouse-clicks etc.
	 */
	public void setFocus() {
		browser.setFocus();
	}
}

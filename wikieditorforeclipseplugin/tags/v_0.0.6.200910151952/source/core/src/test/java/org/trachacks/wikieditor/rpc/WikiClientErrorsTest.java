/**
 * 
 */
package org.trachacks.wikieditor.rpc;


import static org.junit.Assert.*;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.net.URL;

import org.apache.commons.lang.RandomStringUtils;
import org.apache.commons.lang.math.RandomUtils;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.trachacks.wikieditor.AbstractBaseTest;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PageNotModifiedException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;

/**
 * @author ivan
 *
 */
public class WikiClientErrorsTest extends AbstractBaseTest{

	private static String randomTestPageName = RandomStringUtils.randomAlphabetic(10);
	private static String pageContent = "== Title ==\n & % $ á ö / \n 123\n.\n < >\n";
	
	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUp() throws Exception {

	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDown() throws Exception {
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageVersion(java.lang.String)}.
	 * @throws Exception 
	 */
	@Test
	public final void testPageNotFound() throws Exception {
		ServerDetails server = getTestServer();
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		PageVersion pageVersion = null;
		try {
			pageVersion = wikiClient.getPageVersion(randomTestPageName + randomTestPageName);
			fail("Page Not Found didn't throw Exception");
		} catch (PageNotFoundException e) {
		}
		assertNull(pageVersion);
	}
	
	@Test
	public void testUnknownServer() throws Exception {
		ServerDetails server = getTestServer();
		server.setUrl(new URL(getSetting("serverUnknown.url")));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof UnknownServerException);
		}
		
	}
	
	@Test
	public void testConnectionRefused() throws Exception {
		ServerDetails server = getTestServer();
		server.setUrl(new URL(getSetting("connectionRefused.url")));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof ConnectionRefusedException);
		}
		
	}
	
	@Test
	public final void testBadCredentials() throws Exception {
		ServerDetails server = getTestServer();
		server.setUrl(new URL(getSetting("badCredentials.url")));
		server.setUsername(getSetting("badCredentials.username"));
		server.setPassword(getSetting("badCredentials.password"));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof BadCredentialsException);
		}
	}
	
	@Test
	public final void testPermissionDenied() throws Exception {
		ServerDetails server = getTestServer();
		server.setUrl(new URL(getSetting("permissionDenied.url")));
		server.setUsername(getSetting("permissionDenied.username"));
		server.setPassword(getSetting("permissionDenied.password"));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof PermissionDeniedException);
		}
	}
	
	@Test
	public final void testWikiDeletePermissionDenied() throws Exception {
		ServerDetails server = getTestServer();
		server.setUsername(getSetting("wiki_delete.permissionDenied.username"));
		server.setPassword(getSetting("wiki_delete.permissionDenied.password"));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);	
		String pageToDeleteName = randomTestPageName + RandomStringUtils.randomAlphabetic(10);
		String pageContent = this.pageContent  + System.currentTimeMillis();
		try {
			wikiClient.savePageVersion(pageToDeleteName, pageContent, "comment");
			wikiClient.deletePage(pageToDeleteName);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof PermissionDeniedException);
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#savePageVersion(java.lang.String, java.lang.String, java.lang.String, int, boolean)}.
	 */
	@Test
	public final void testPageNotModifiedException() throws Exception {
		ServerDetails server = getTestServer();
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);
		String pageName = randomTestPageName + RandomStringUtils.randomAlphabetic(10);
		String editedContent = pageContent + RandomStringUtils.randomAlphabetic(10);
		PageVersion pageVersion = wikiClient.savePageVersion(pageName, editedContent, "First Edit");
		assertNotNull(pageVersion);
		assertEquals("PageName", pageName, pageVersion.getName());
		assertEquals("Contents", editedContent, pageVersion.getContent());
		assertEquals("Version", (int)1, (int)pageVersion.getVersion());
		try {
			wikiClient.savePageVersion(pageName, editedContent, "Second Edit");
			fail("PageNotModifiedException not thrown");
		} catch (Exception e) {
			assertTrue("PageNotModified Exception", e instanceof PageNotModifiedException);
		}
	}
}

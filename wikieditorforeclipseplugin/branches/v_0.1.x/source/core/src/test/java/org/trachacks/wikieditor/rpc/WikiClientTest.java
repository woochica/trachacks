/**
 * 
 */
package org.trachacks.wikieditor.rpc;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.net.URL;
import java.util.Date;
import java.util.List;

import org.apache.commons.lang.RandomStringUtils;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.trachacks.wikieditor.AbstractBaseTest;
import org.trachacks.wikieditor.model.PageInfo;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.ConcurrentEditException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;

/**
 * @author ivan
 *
 */
public class WikiClientTest extends AbstractBaseTest{

	private static String randomTestPageName = RandomStringUtils.randomAlphabetic(10);
	private static String pageContent = "== Title ==\n & % $ á ö / \n 123\n.\n < >\n";
	private WikiClient wikiClient;
	
	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUpBefore() throws Exception {
		ServerDetails server = new ServerDetails();
		server.setUrl(new URL(getSetting("server.url")));
		
		server.setUsername(getSetting("credentials.username"));
		server.setPassword(getSetting("credentials.password"));
		
		wikiClient = new WikiClientImpl(server, proxySettings);
	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDownAfter() throws Exception {
		wikiClient = null;
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageNames()}.
	 * @throws Exception
	 */
	@Test
	public final void testGetPageNames() throws Exception {
		String[] pageNames = wikiClient.getPageNames();
		for (int i = 0; i < pageNames.length; i++) {
			String pageName = pageNames[i];
			assertNotNull(pageName);
		}
	}
	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageVersion(java.lang.String)}.
	 */
	@Test
	public final void testPageNotFound() {
		PageVersion pageVersion = null;
		try {
			pageVersion = wikiClient.getPageVersion(randomTestPageName + randomTestPageName);
			fail("Page Not Found didn't throw Exception");
		} catch (PageNotFoundException e) {
		}
		assertNull(pageVersion);
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#savePageVersion(java.lang.String, java.lang.String, java.lang.String, int, boolean)}.
	 */
	@Test
	public final void testSavePageVersion() {
		PageVersion pageVersion = wikiClient.savePageVersion(randomTestPageName, pageContent, "First Edit");
		assertNotNull(pageVersion);
		assertEquals("PageName", randomTestPageName, pageVersion.getName());
		assertEquals("Contents", pageContent, pageVersion.getContent());
		assertEquals("Version", (int)1, (int)pageVersion.getVersion());
	}

	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#savePageVersion(java.lang.String, java.lang.String, java.lang.String, int, boolean)}.
	 */
	@Test
	public final void testConcurentEdits() {
		PageVersion pageVersion = wikiClient.getPageVersion(randomTestPageName);

		wikiClient.savePageVersion(pageVersion.getName(), "Edit" + pageVersion.getContent(), "Edit");
		
		try {
			wikiClient.savePageVersion(pageVersion.getName(), "Concurrent: " + pageVersion.getContent(), "Concurrent Edit", pageVersion.getVersion() -1, false);
			fail("Successful Concurrent Edit is an error");
		}catch(Exception e) {
			assertTrue("ConcurrentEditException", e instanceof ConcurrentEditException);
		}

		wikiClient.savePageVersion(pageVersion.getName(), "Another Edit" + pageVersion.getContent(), "Another Edit");

	}

	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageVersion(java.lang.String)}.
	 */
	@Test
	public final void testGetPageVersionByName() {
		PageVersion pageVersion = wikiClient.getPageVersion(randomTestPageName);
		assertNotNull(pageVersion);
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageVersion(java.lang.String, int)}.
	 */
	@Test
	public final void testGetPageVersionCustomVersion() {
		PageVersion pageVersion = wikiClient.getPageVersion(randomTestPageName, 1);
		assertNotNull(pageVersion);
	}


	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageHistory(java.lang.String)} 
	 * and {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getPageHistory(java.lang.String, int, int)}..
	 */
	@Test
	public final void testGetPageHistoryString() {
		List<PageInfo> pageHistory = wikiClient.getPageHistory(randomTestPageName);
		for (PageInfo pageInfo : pageHistory) {
			assertNotNull(pageInfo);
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.WikiClientImpl#getRecentChanges(java.util.Date)} 
	 */
	@Test
	public final void testGetRecentChanges() {
		List<PageInfo> recentChanges = wikiClient.getRecentChanges(new Date(0));
		for (PageInfo pageInfo : recentChanges) {
			assertNotNull(pageInfo);
		}
	}
}

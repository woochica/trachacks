/**
 * 
 */
package org.trachacks.wikieditor.service;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.File;
import java.net.URL;
import java.util.Date;
import java.util.List;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.trachacks.wikieditor.AbstractBaseTest;
import org.trachacks.wikieditor.model.PageInfo;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.ConcurrentEditException;

/**
 * @author ivan
 *
 */
public class WikiServiceTest extends AbstractBaseTest{

	private static Long testServerId = System.currentTimeMillis();
	private static String randomTestPageName = "" + System.currentTimeMillis();
	private static String pageContent = "== Title ==\n & % $ á ö / \n 123\n.\n < >\n";
	private WikiService wikiService;
	
	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUpBefore() throws Exception {
		ServerDetails server = new ServerDetails();
		server.setId(testServerId);
		server.setUrl(new URL(getSetting("server.url")));
		
		server.setUsername(getSetting("credentials.username"));
		server.setPassword(getSetting("credentials.password"));
		
		ServiceFactory.setCacheFolder(new File("target/tests/cache"));
		wikiService = ServiceFactory.getWikiService(server);
	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDownAfter() throws Exception {
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#loadPages()}.
	 */
	@Test
	public final void testLoadPages() {
		List<PageInfo> pages = wikiService.loadPages();
		assertNotNull(pages);
		for (PageInfo pageInfo : pages) {
			assertNotNull(pageInfo);
		}
	}
	
	@Test
	public final void testSavePage() {
		PageVersion pageVersion = wikiService.loadPageVersion(randomTestPageName);
		pageVersion.setContent(pageContent);
		pageVersion.setComment("First Edit!");
		pageVersion = wikiService.commit(pageVersion);
		assertEquals("Version", (int)1, (int) pageVersion.getVersion());
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#loadPageVersion(java.lang.String)}.
	 */
	@Test
	public final void testLoadPageVersionString() {
		PageVersion pageVersion = wikiService.loadPageVersion(randomTestPageName);
		assertNotNull(pageVersion);
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#edit(org.trachacks.wikieditor.model.PageVersion)}.
	 */
	@Test
	public final void testEdit() {
		PageVersion firstVersion = wikiService.loadPageVersion(randomTestPageName);
		firstVersion.setContent("Some text here..." + System.currentTimeMillis());
		firstVersion.setComment("Local non commited Edit");
		
		PageVersion afterEditVersion = wikiService.edit(firstVersion);
		
		PageVersion originalVersion = wikiService.getLatestVersion(randomTestPageName);
		
		assertTrue("Edited?", afterEditVersion.isEdited());
		assertEquals("After Edit Version", firstVersion.getVersion(), afterEditVersion.getVersion());
		assertEquals("Original Version", firstVersion.getVersion(), originalVersion.getVersion());
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#getPageNames()}
	 */
	@Test
	public final void testGetPageNames() {
		String[] pageNames = wikiService.getPageNames();
		for (int i = 0; i < pageNames.length; i++) {
			String string = pageNames[i];
		}
	}
	
	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#commit(org.trachacks.wikieditor.model.PageVersion)}.
	 */
	@Test
	public final void testCommit() {
		PageVersion editedVersion = wikiService.loadPageVersion(randomTestPageName);
		PageVersion latestVersion = wikiService.getLatestVersion(randomTestPageName);
		assertTrue("Edited?", editedVersion.isEdited());
		assertEquals("Edited Version", editedVersion.getVersion(), latestVersion.getVersion());
		
		PageVersion commitedVersion = wikiService.commit(editedVersion);
		assertFalse("Edited?", commitedVersion.isEdited());
		
		latestVersion = wikiService.getLatestVersion(randomTestPageName);
		assertEquals("Commited Version", commitedVersion.getVersion(), latestVersion.getVersion());
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#unedit(org.trachacks.wikieditor.model.PageVersion)}.
	 */
	@Test
	public final void testUnedit() {
		this.testEdit();
		PageVersion editedVersion = wikiService.loadPageVersion(randomTestPageName);
		assertTrue("Edited?", editedVersion.isEdited());
		PageVersion unEditedVersion = wikiService.unedit(editedVersion);
		assertFalse("UnEdited?", unEditedVersion.isEdited());
		
		PageVersion latestVersion = wikiService.getLatestVersion(randomTestPageName);
		assertEquals("UnEdited Version", unEditedVersion.getVersion(), latestVersion.getVersion());
		
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#forceCommit(org.trachacks.wikieditor.model.PageVersion)}.
	 */
	@Test
	public final void testForceCommit() {
		PageVersion pageVersion = wikiService.loadPageVersion(randomTestPageName);
		int originalVersion = pageVersion.getVersion();
		pageVersion.setContent("Some text here..." + System.currentTimeMillis());
		pageVersion.setComment("Local non commited Edit");
		pageVersion.setVersion(originalVersion - 1);
		
		PageVersion commitedVersion = null;
		
		try {
			commitedVersion = wikiService.commit(pageVersion);
			fail("Concurrent Edit  Succeded");
		} catch (ConcurrentEditException e) {
			commitedVersion = wikiService.forceCommit(pageVersion);
			assertNotNull(commitedVersion);
			assertEquals("Commited Version", (int)(originalVersion + 1), (int)commitedVersion.getVersion());
		}
	}

	
	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#getPageHistory(java.lang.String)}.
	 */
	@Test
	public final void testGetPageHistory() {
		List<PageInfo> pageHistory = wikiService.getPageHistory(randomTestPageName);
		for (PageInfo pageInfo : pageHistory) {
			assertNotNull(pageInfo);
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#loadPageVersion(java.lang.String, int)}.
	 */
	@Test
	public final void testLoadPageVersionStringInt() {
		PageVersion pageVersion = wikiService.loadPageVersion(randomTestPageName, 2);
		assertNotNull(pageVersion);
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiServiceImpl#getRecentChanges(Date)} 
	 */
	@Test
	public final void testGetRecentChanges() {
		List<PageInfo> recentChanges = wikiService.getRecentChanges(null); // returns all changes since epoc
		for (PageInfo pageInfo : recentChanges) {
			assertNotNull(pageInfo);
		}
	}
	
	/**
	 * Test method for {@link org.trachacks.wikieditor.service.WikiService#deletePage(String)}
	 * and {@link org.trachacks.wikieditor.service.WikiService#deletePageVersion(String, int)}.
	 */
	@Test	
	public final void testZDeletePage() {
		this.testEdit();
		boolean success = wikiService.deletePageVersion(randomTestPageName, 2);
		assertTrue("Delete Page Version", success);
		success = wikiService.deletePage(randomTestPageName);
		assertTrue("Delete Page", success);
	}

}

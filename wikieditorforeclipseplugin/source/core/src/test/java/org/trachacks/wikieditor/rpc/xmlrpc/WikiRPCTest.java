/**
 * 
 */
package org.trachacks.wikieditor.rpc.xmlrpc;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.net.URL;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import org.apache.commons.lang.StringUtils;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.trachacks.wikieditor.AbstractBaseTest;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public class WikiRPCTest extends AbstractBaseTest{

	private WikiRPC client = null;
	private static String testPageName = "TestPage" + System.currentTimeMillis();
	private String testPageContents = "Some Content";
	private String testPageUpdatedContents = "Some Updated Contents";
	
	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUp() throws Exception {
		ServerDetails server = new ServerDetails();
		server.setUrl(new URL(getSetting("server.url")));
		
		server.setUsername(getSetting("credentials.username"));
		server.setPassword(getSetting("credentials.password"));
		
		client = WikiRPCClientFactory.getWikiRPCClientInstance(server, proxySettings);
	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDown() throws Exception {
		client = null;
	}

	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getRPCVersionSupported()}.
	 */
	@Test
	public final void testGetRPCVersionSupported() {
		int supportedVersion = client.getRPCVersionSupported();
		assertTrue("Server does not support this API version", supportedVersion >= WikiRPC.RPC_API_VERSION);
	}
	

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#putPage(java.lang.String, java.lang.String, java.util.Map)}.
	 */
	@Test
	public final void testPutPage() {
		client.putPage(testPageName, testPageContents, new HashMap());
	}
	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getPage(java.lang.String)}.
	 */
	@Test
	public final void testGetPage() {
		String pageContent = client.getPage(testPageName);
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#putPage(java.lang.String, java.lang.String, java.util.Map)}.
	 */
	@Test
	public final void testUpdatePage() {
		try {
			client.putPage(testPageName, testPageContents, new HashMap());
			fail("Page Not Modified update didn't fail as expected");
		}
		catch(Exception exception) {
			
		}
		client.putPage(testPageName, testPageUpdatedContents, new HashMap());
	}
	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getPageVersion(java.lang.String, int)}.
	 */
	@Test
	public final void testGetPageVersion() {
		String version1 = client.getPageVersion(testPageName, 1);
		assertTrue("test Page First Version Content does not match", testPageContents.equals(version1));
		
		String version2 = client .getPageVersion(testPageName, 2);
		assertTrue("test Page First Version Content does not match", testPageUpdatedContents.equals(version2));
		
		try {
			String version3 = client .getPageVersion(testPageName, 3);
			fail("Gettings inexisting page version didn't fail...");
		}
		catch(Exception e) {
			
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getAllPages()}.
	 */
	@Test
	public final void testGetAllPages() {
		Object[] pages = client.getAllPages();
		for (int i = 0; i < pages.length; i++) {
			String page = (String) pages[i];
			assertNotNull(page);
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getPageInfo(java.lang.String)}.
	 */
	@Test
	public final void testGetPageInfo() {
		Map<String, Object> pageInfo = client.getPageInfo(testPageName);
		for (Map.Entry<String, Object> property : pageInfo.entrySet()) {
			assertNotNull(property.getKey());
			assertNotNull(property.getValue());
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getPageInfoVersion(java.lang.String, int)}.
	 */
	@Test
	public final void testGetPageInfoVersion() {
		Map<String, Object> pageInfo = client.getPageInfoVersion(testPageName, 1);
		for (Map.Entry<String, Object> property : pageInfo.entrySet()) {
			assertNotNull(property.getKey());
			assertNotNull(property.getValue());
		}
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#deletePage(String)} and 
	 * {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#deletePage(String, int)}.
	 */
	@Test
	public final void testDeletePage() {
		boolean success = client.deletePage(testPageName, 1);
		assertTrue("Delete Page Version 1", success);
		
		success = client.deletePage(testPageName);
		assertTrue("Delete Page All Version", success);
	}

	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#getRecentChanges(java.util.Date)}.
	 */
	@Test	
	public final void testGetRecentChanges() {
		try {
			client.getRecentChanges(null);
			fail("Null param should throw an XML-RPC exception");
		} catch (Exception e) {
		}
		
		Object[] changes = client.getRecentChanges(new Date(0));
		for (int i = 0; i < changes.length; i++) {
			Map<String, Object> pageInfo = (Map<String, Object>) changes[i];
			for (Map.Entry<String, Object> property : pageInfo.entrySet()) {
				//System.out.println(property.getKey() + "=" + property.getValue());
				assertNotNull(property.getKey());
				assertNotNull(property.getValue());
			}			
		}
	}
	
	/**
	 * Test method for {@link org.trachacks.wikieditor.rpc.xmlrpc.WikiRPC#wikiToHtml(java.lang.String)}.
	 */
	@Test
	public final void testWikiToHtml() {
		String html = client.wikiToHtml(testPageName);
		assertTrue("Html should not be empty", StringUtils.isNotEmpty(html));
	}

}

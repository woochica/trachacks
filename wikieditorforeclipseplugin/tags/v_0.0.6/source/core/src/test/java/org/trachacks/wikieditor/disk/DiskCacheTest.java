package org.trachacks.wikieditor.disk;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.net.URL;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.trachacks.wikieditor.AbstractBaseTest;
import org.trachacks.wikieditor.disk.impl.DiskCacheImpl;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;

public class DiskCacheTest extends AbstractBaseTest{

	private DiskCache diskCache = new DiskCacheImpl(new File("target/tests/cache"));
	private static String pageName = "TestPage-" + System.currentTimeMillis();
	private static Long serverId = System.currentTimeMillis();
	private static ServerDetails defaultTestServer = null;
	private static String pageContent = "== Title ==\n & % $ á ö / \n 123\n.\n < >\n";
	
	
	@Before
	public void setUpBefore() throws Exception {
		defaultTestServer = new ServerDetails();
		defaultTestServer.setId(serverId);
		defaultTestServer.setName("Default Test Server");
		defaultTestServer.setUrl(new URL(getSetting("server.url")));

		defaultTestServer.setUsername(getSetting("credentials.username"));
		defaultTestServer.setPassword(getSetting("credentials.password"));		
	}

	@After
	public void tearDownAfter() throws Exception {
	}

	
	@Test
	public final void testSaveServers() throws Exception {
		Set<ServerDetails> servers = new HashSet<ServerDetails>();
		for(int i = 0; i < 10; i++) {
			Long id = System.currentTimeMillis() + i;
			ServerDetails server = null;
			// create some servers with password and some anonymous
			if(i%2 == 0) {
				server = new ServerDetails(id,"name" + i, new URL("http://server/url" + i));
			}
			else {
				server = new ServerDetails(id,"name" + i, new URL("http://server/url" + i), "user" + i, "pass" + i);
			}
			servers.add(server);
		}
		diskCache.save(servers);
		assertTrue("Servers size is " + servers.size(), servers.size() == 10);
	}

	@Test
	public final void testLoadServers() throws Exception {
		Set<ServerDetails> servers = diskCache.loadServers();
		int anonymous = 0;
		int nonAnonymous = 0;
		for (ServerDetails serverDetails : servers) {
			if(serverDetails.isAnonymous()) {
				anonymous++;
			}else {
				 nonAnonymous++;
			}
		}
		assertTrue("Anonymouns/Non-Anonymous Servers count does not match", anonymous == nonAnonymous);
		assertTrue(anonymous + nonAnonymous  ==10);
	}

	@Test
	public final void testSavePageVersion() {
		PageVersion page = new PageVersion();
		page.setServerId(serverId);
		page.setName(pageName);
		page.setAuthor("the author");
		page.setComment("the comment");
		page.setDate(new Date());
		page.setContent(pageContent);

		diskCache.save(page);
	}

	@Test
	public final void testLoad() {
		PageVersion page = diskCache.load(serverId, pageName);
		assertNotNull(page);
		assertTrue("Server Id Does Not Match", serverId.equals(page.getServerId()));
		assertTrue("Page Name Does Not Match", pageName.equals(page.getName()));
		assertTrue("Page Content Does Not Match", pageContent.equals(page.getContent()));
	}

	@Test
	public final void testRemove() {
		diskCache.remove(serverId, pageName);
		PageVersion page = diskCache.load(serverId, pageName);
		assertNull(page);
	}

}

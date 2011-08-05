/**
 * 
 */
package org.trachacks.wikieditor.rpc.proxy;


import static org.junit.Assert.*;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.net.URL;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.trachacks.wikieditor.AbstractBaseTest;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.model.exception.BadCredentialsException;
import org.trachacks.wikieditor.model.exception.ConnectionRefusedException;
import org.trachacks.wikieditor.model.exception.GatewayTimeoutException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PageNotModifiedException;
import org.trachacks.wikieditor.model.exception.PermissionDeniedException;
import org.trachacks.wikieditor.model.exception.ProxyAuthenticationRequiredException;
import org.trachacks.wikieditor.model.exception.UnknownServerException;
import org.trachacks.wikieditor.rpc.WikiClient;
import org.trachacks.wikieditor.rpc.WikiClientImpl;

/**
 * @author ivan
 *
 */
public class WikiClientErrorsThroughProxyTestNoAuto extends org.trachacks.wikieditor.rpc.WikiClientErrorsTest{
	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUpBefore() throws Exception {
		loadProxySettings();
	}

	@Override	@Test
	public void testUnknownServer() throws Exception {
		ServerDetails server = getTestServer();
		server.setUrl(new URL(getSetting("serverUnknown.url")));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof GatewayTimeoutException);
		}
		
	}
	
	@Override @Test
	public void testConnectionRefused() throws Exception {
		ServerDetails server = getTestServer();
		server.setUrl(new URL(getSetting("connectionRefused.url")));
		WikiClient wikiClient = new WikiClientImpl(server, proxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof GatewayTimeoutException);
		}
		
	}
	
	@Test
	public final void testProxyAuthRequired() throws Exception {
		ServerDetails server = getTestServer();
		ProxySettings anonProxySettings = new ProxySettings(proxySettings.getProxyHost(), proxySettings.getProxyPort());
		WikiClient wikiClient = new WikiClientImpl(server, anonProxySettings);		

		try {
			wikiClient.testConnection(server, proxySettings);
			fail("Exception");
		} catch (Exception e) {
			assertTrue("Caugth Exception: " + e.getClass(), e instanceof ProxyAuthenticationRequiredException);
		}
	}
}

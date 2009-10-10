/**
 * 
 */
package org.trachacks.wikieditor.service;

import java.io.File;

import org.trachacks.wikieditor.model.ProxySettings;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public class ServiceFactory {

	private static File cacheFolder;

	public static void setCacheFolder(File folder) {
		cacheFolder = folder;
		if(cacheFolder != null) {
			cacheFolder.mkdirs();
		}
	}
	
	static { // set sensible defaults
		cacheFolder = new File(System.getProperty("java.io.tmpdir"));
		cacheFolder.mkdirs();
	}
	
	public static synchronized WikiService getWikiService(ServerDetails server) {
		return new WikiServiceImpl(server, cacheFolder);
	}
	
	public static synchronized WikiService getWikiService(ServerDetails server, ProxySettings proxySettings) {
		return new WikiServiceImpl(server, cacheFolder, proxySettings);
	}
}


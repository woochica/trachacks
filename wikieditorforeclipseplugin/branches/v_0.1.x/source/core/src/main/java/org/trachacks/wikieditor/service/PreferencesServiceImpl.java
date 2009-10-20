/**
 * 
 */
package org.trachacks.wikieditor.service;

import java.io.File;
import java.util.Set;

import org.apache.commons.lang.BooleanUtils;
import org.trachacks.wikieditor.disk.DiskCache;
import org.trachacks.wikieditor.disk.impl.DiskCacheImpl;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public class PreferencesServiceImpl implements PreferencesService {
	
	private DiskCache diskCache;

	public PreferencesServiceImpl() {
		super();
	}

	public PreferencesServiceImpl(File cacheFolder) {
		super();
		diskCache = new DiskCacheImpl(cacheFolder);
	}

	public void setDiskCache(DiskCache diskCache) {
		this.diskCache = diskCache;
	}
	
	

	/**
	 * @see org.trachacks.wikieditor.service.PreferencesService#addServer(org.trachacks.wikieditor.model.ServerDetails)
	 */
	public ServerDetails addServer(ServerDetails server) {
		Set<ServerDetails> servers = diskCache.loadServers();
		if(server.getId() == null) {
			server.setId(System.currentTimeMillis());
		}
		servers.add(server);
		diskCache.save(servers);
		return server;
	}

	/**
	 * 
	 */
	public ServerDetails updateServer(ServerDetails serverDetails) {
		Set<ServerDetails> servers = diskCache.loadServers();
		servers.remove(serverDetails);
		servers.add(serverDetails);
		diskCache.save(servers);
		return serverDetails;
	}
	
	/**
	 * @see org.trachacks.wikieditor.service.PreferencesService#loadServerList()
	 */
	public Set<ServerDetails> loadServerList() {
		return diskCache.loadServers();
	}

	/**
	 * @see org.trachacks.wikieditor.service.PreferencesService#removeServer(java.lang.Long)
	 */
	public void removeServer(ServerDetails server) {
		Set<ServerDetails> servers = diskCache.loadServers();
		servers.remove(server);
		diskCache.save(servers);
	}

}

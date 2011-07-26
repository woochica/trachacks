/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.model;

import java.io.File;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import org.trachacks.wikieditor.model.ServerDetails;
import org.trachacks.wikieditor.service.PreferencesService;
import org.trachacks.wikieditor.service.PreferencesServiceImpl;

/**
 * @author ivan
 *
 */
public class ServerList extends AbstractBaseObject implements Iterable<Server> {

	private static ServerList instance = new ServerList();
	
	private PreferencesService preferencesService;
	private Map<Long, Server> servers = new HashMap<Long, Server>();
	
	/**
	 * 
	 * @param servers
	 */
	private ServerList() {
		super();
		File pluginFolder = org.trachacks.wikieditor.eclipse.plugin.Activator.getDefault().getStateLocation().toFile();
		preferencesService = new PreferencesServiceImpl(pluginFolder);
		Collection<ServerDetails> servers = preferencesService.loadServerList();
		for (ServerDetails serverDetails : servers) {
			this.servers.put(serverDetails.getId(), new Server(serverDetails));
		}
	}
	
	/**
	 * 
	 * @return
	 */
	public static ServerList getInstance() {
		return instance;
	}

	/**
	 * 
	 */
	public Iterator<Server> iterator() {
		return servers.values().iterator();
	}
	
	public Server[] getServers() {
		return servers.values().toArray(new Server[servers.size()]);
	}


	public ServerDetails getServerDetails(Long serverId) {
		return servers.get(serverId).getServerDetails();
	}

	/**
	 * 
	 * @param serverDetails
	 * @see org.trachacks.wikieditor.service.PreferencesService#updateServer(ServerDetails)
	 */
	public void updateServerDetails(ServerDetails serverDetails) {
		Server server = servers.get(serverDetails.getId());
		server.disconnect();
		serverDetails = preferencesService.updateServer(serverDetails);
		server.setServerDetails(serverDetails);
		server.notifyChanged();
		notifyChanged();
	}
	
	/**
	 * @param arg0
	 * @see org.trachacks.wikieditor.service.PreferencesService#addServer(org.trachacks.wikieditor.model.ServerDetails)
	 */
	public void addServer(ServerDetails serverDetails) {
		serverDetails = preferencesService.addServer(serverDetails);
		servers.put(serverDetails.getId(), new Server(serverDetails));
		notifyChanged();
	}

	/**
	 * @param arg0
	 * @see org.trachacks.wikieditor.service.PreferencesService#removeServer(org.trachacks.wikieditor.model.ServerDetails)
	 */
	public void removeServer(ServerDetails serverDetails) {
		servers.remove(serverDetails.getId());
		preferencesService.removeServer(serverDetails);
		notifyChanged();
	}

	
	
}

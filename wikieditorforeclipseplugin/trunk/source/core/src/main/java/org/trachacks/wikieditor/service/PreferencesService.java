/**
 * 
 */
package org.trachacks.wikieditor.service;

import java.util.Set;

import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public interface PreferencesService {

	public Set<ServerDetails> loadServerList();
	public ServerDetails addServer(ServerDetails server);
	public ServerDetails updateServer(ServerDetails serverDetails);
	public void removeServer(ServerDetails server);
}

/**
 * 
 */
package org.trachacks.wikieditor.disk;

import java.util.Set;

import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.ServerDetails;

/**
 * @author ivan
 *
 */
public interface DiskCache {

	public void save(Set<ServerDetails> servers);
	public Set<ServerDetails> loadServers();
	
	public void save(PageVersion pageVersion);
	public String[] getCachedPageNames(Long serverId);
	public PageVersion load(Long serverId, String pageName);
	public void remove(Long serverId, String pageName);
}

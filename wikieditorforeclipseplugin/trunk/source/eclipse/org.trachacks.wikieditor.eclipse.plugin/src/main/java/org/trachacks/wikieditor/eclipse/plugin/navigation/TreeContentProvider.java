/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.navigation;

import java.util.List;

import org.eclipse.jface.viewers.IStructuredContentProvider;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.Viewer;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.eclipse.plugin.model.Server;
import org.trachacks.wikieditor.eclipse.plugin.model.ServerList;
import org.trachacks.wikieditor.eclipse.plugin.model.util.IModelChangeListener;
import org.trachacks.wikieditor.model.PageInfo;

/**
 * @author ivan
 *
 */
public class TreeContentProvider implements IStructuredContentProvider, ITreeContentProvider {
	
	private IModelChangeListener modelChangeListener;

	/**
	 * @param parent
	 */
	public TreeContentProvider(IModelChangeListener parent) {
		super();
		this.modelChangeListener = parent;
	}

	public Object[] getElements(Object parent) {
		return getChildren(parent);
	}

	public void dispose() {
	}

	public void inputChanged(Viewer arg0, Object arg1, Object arg2) {
	}

	/**
	 * 
	 */
	public Object[] getChildren(Object obj) {
		if(obj instanceof ServerList) {
			Server[] servers = ((ServerList) obj).getServers();
			for (int i = 0; i < servers.length; i++) {
				servers[i].addListener(modelChangeListener);
			}
			return servers;
		}
		else if(obj instanceof Server) {
			if(((Server)obj).isConnected()) {
				List<Page> pages = ((Server)obj).getPages();
				for (Page page : pages) {
					page.addListener(modelChangeListener);
				}
				return pages.toArray(new Page[0]);
			}
			else {
				return null;
			}
		}
		else if(obj instanceof Page) {
			return null;
		}
		return null;
	}

	/**
	 * 
	 */
	public Object getParent(Object obj) {
		if(obj instanceof Server) {
			return ServerList.getInstance();
		}
		else if(obj instanceof Page) {
			return ((Page) obj).getServer();
		}
		return null;
	}

	public boolean hasChildren(Object obj) {
		if(obj instanceof ServerList) {
			return ServerList.getInstance().getServers() != null;
		}
		else if(obj instanceof Server) {
			return ((Server) obj).isConnected() && !((Server) obj).getPages().isEmpty();
		}
		else if(obj instanceof Page) {
			return false;
		}
		return getChildren(obj) != null;
	}

}

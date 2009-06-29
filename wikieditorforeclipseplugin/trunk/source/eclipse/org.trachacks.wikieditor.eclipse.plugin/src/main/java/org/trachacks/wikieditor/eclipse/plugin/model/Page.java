/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.model;

import java.util.ArrayList;
import java.util.List;

import org.trachacks.wikieditor.model.PageInfo;
import org.trachacks.wikieditor.model.PageVersion;
import org.trachacks.wikieditor.model.exception.ConcurrentEditException;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;
import org.trachacks.wikieditor.model.exception.PageNotModifiedException;
import org.trachacks.wikieditor.model.exception.PageVersionNotFoundException;
import org.trachacks.wikieditor.service.WikiService;

/**
 * @author ivan
 *
 */
public class Page extends AbstractBaseObject {

	private String name;
	private Server server;

	private String shortName;
	private Page parent;
	private List<Page> children = new ArrayList<Page>();
	
	private boolean wasDeleted;
	private boolean isFolder = true;
	private boolean isEditedConcurrently;
	
	private PageVersion baseVersion = null;
	
	/**
	 * @param server
	 */
	Page(Server server, String name) throws PageNotFoundException{
		super();
		this.name = name;
		this.server = server;
		this.shortName = name.substring(name.lastIndexOf('/') +1);
//		this.wikiService = ServiceFactory.getWikiService(server.getServerDetails());
		
		if(getWikiService().isLocallyEdited(name)) {
			this.baseVersion = getWikiService().loadPageVersion(name);
		}
		refreshAttributes();
	}
	
	public String getShortName() {
		return shortName;
	}

	public Page getParent() {
		return parent;
	}

	public List<Page> getChildren() {
		return children;
	}

	public List<Page> addChild(Page child) {
		children.add(child);
		child.parent = this;
		return children;
	}

//	public void setServer(Server server) {
//		this.server = server;
//	}

	/**
	 * @return the name
	 */
	public String getName() {
		return name;
	}

	public String getDescription() {
		StringBuffer description = new StringBuffer();
		description.append(server.getServerDetails().getName());
		description.append("[");   //$NON-NLS-1$
		description.append(server.getServerDetails().getUrl());
		description.append("] > ");   //$NON-NLS-1$
		description.append(name);
		return description.toString();
	}

	/**
	 * @return this page server
	 */
	public Server getServer() {
		return server;
	}

	/**
	 * 
	 * @return
	 */
	public PageVersion load() throws PageNotFoundException{
		PageVersion version =  getWikiService().loadPageVersion(name);
//		if(version.isEdited()) {
			baseVersion = version;
//		}
		return version;
	}
	
	public void refresh() {
		refreshAttributes();
		refreshTree();
		super.notifyChanged();
	}
	
	/**
	 * 
	 */
	public void refreshAttributes() {
		try {
			this.wasDeleted =  isEdited() && getLatestVersion() == null;
		} catch (PageNotFoundException e) {
			this.wasDeleted =  isEdited() && !isBrandNew();
		}
		
		this.isEditedConcurrently =  isEdited()
		&& !isBrandNew()
		&& !wasDeleted
		&& (int)getLatestVersion().getVersion() != (int)baseVersion.getVersion();

	}
	
	public void refreshTree() {
		children = server.getPageChildren(name);
	}
	
	public PageVersion getBaseVersion() {
		return baseVersion;
	}
	
	/**
	 * 
	 * @return
	 */
	public boolean isEdited() {
		return baseVersion != null && baseVersion.isEdited() 
						|| getWikiService().isLocallyEdited(name);
	}
	
	public boolean isBrandNew() {
		return isEdited() && baseVersion.getVersion() < 1;
	}
	
	public boolean isEditedConcurrently() {
		return isEditedConcurrently;
	}
	
	public boolean wasDeleted() {
		return wasDeleted;
	}
	
	public void setIsFolder(boolean isFolder) {
		this.isFolder = isFolder;
	}
	
	public boolean isFolder() {
		return isFolder;
	}
	
	/**
	 * @param arg0
	 * @return
	 * @see org.trachacks.wikieditor.service.WikiService#edit(org.trachacks.wikieditor.model.PageVersion)
	 */
	public PageVersion edit(String content) {
		isFolder = false;
		baseVersion.setContent(content);
		baseVersion.setEdited(true);
		baseVersion = getWikiService().edit(baseVersion);
		notifyChanged();
		return baseVersion;
	}
	
	/**
	 * Commit a non minor edit.
	 * 
	 * @param comment
	 * @throws ConcurrentEditException
	 * 
	 * @see {@link #commit(String, boolean)} for isMinorEdit = false
	 */
	public void commit(String comment) throws ConcurrentEditException, PageNotModifiedException {
		commit(comment, false);
	}

	
	/**
	 * 
	 * @return
	 * @throws ConcurrentEditException
	 * @see org.trachacks.wikieditor.service.WikiService#commit(org.trachacks.wikieditor.model.PageVersion)
	 */
	public void commit(String comment, boolean isMinorEdit) throws ConcurrentEditException, PageNotModifiedException {
		baseVersion.setComment(comment);
		this.baseVersion = getWikiService().commit(baseVersion, isMinorEdit);
		notifyChanged();
	}

	/**
	 * 
	 * @return
	 * @see org.trachacks.wikieditor.service.WikiService#forceCommit(org.trachacks.wikieditor.model.PageVersion)
	 */
	public void forceCommit(String comment) throws PageNotModifiedException {
		baseVersion.setComment(comment);
		getWikiService().forceCommit(baseVersion);
		this.baseVersion = null;
		notifyChanged();
	}
	
	/**
	 * 
	 * @param mergedText
	 * @param mergedVersionNumber
	 */
	public void markAsMerged(int mergedVersionNumber) {
		baseVersion.setVersion(mergedVersionNumber);
		getWikiService().edit(baseVersion);
		notifyChanged();
	}

	/**
	 * 
	 * @return
	 * @see org.trachacks.wikieditor.service.WikiService#unedit(org.trachacks.wikieditor.model.PageVersion)
	 */
	public void unedit() {
		boolean isBrandNew = isBrandNew();
		try {
			getWikiService().unedit(baseVersion);
		} catch (PageNotFoundException e) {
			this.server.notifyChanged(); // unedit a deleted page
		}
		this.baseVersion = null;
		if(isBrandNew) {
			if(parent != null) {
				parent.refresh();
			} else {
				server.refresh();
			}
		}
		notifyChanged();
	}

	
	/**
	 * 
	 * @return
	 */
	public PageVersion getLatestVersion() {
		return getWikiService().getLatestVersion(name);
	}
	
	public PageVersion getVersion(int version) throws PageVersionNotFoundException {
		return getWikiService().loadPageVersion(name, version);
	}
	
	/**
	 * @param arg0
	 * @return
	 * @throws PageNotFoundException
	 * @see org.trachacks.wikieditor.service.WikiService#getPageHistory(java.lang.String)
	 */
	public List<PageInfo> getPageHistory() {
		return getWikiService().getPageHistory(name);
	}

	public String wikiToHtml(String wikiText) {
		return getWikiService().wikiToHtml(wikiText);
	}
	
	
	/**
	 * 
	 * @return
	 */
	protected WikiService getWikiService() {
		return server.getWikiService();
	}


	@Override
	protected void notifyChanged() {
		refresh();
		super.notifyChanged();
	}
	
	
	
}

/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.apache.commons.lang.builder.CompareToBuilder;
import org.eclipse.core.resources.IStorage;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.ui.IPersistableElement;
import org.eclipse.ui.IStorageEditorInput;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

/**
 * @author ivan
 *
 */
public class WikiPageEditorInput implements IStorageEditorInput {

	private Page page;
	private IStorage storage;

	/**
	 * 
	 * @param page
	 */
	public WikiPageEditorInput(Page page) {
		super();
		this.page = page;
		this.storage = new WikiPageEditorStorage(page);
	}

	/**
	 * @see org.eclipse.ui.IStorageEditorInput#getStorage()
	 */
	public IStorage getStorage() throws CoreException {
		return storage;
	}

	/**
	 * @see org.eclipse.ui.IEditorInput#exists()
	 */
	public boolean exists() {
		return !page.isBrandNew(); // XXX
	}

	/**
	 * @see org.eclipse.ui.IEditorInput#getImageDescriptor()
	 */
	public ImageDescriptor getImageDescriptor() {
		return Images.getDescriptor(Images.TRAC_16);
	}

	/**
	 * @see org.eclipse.ui.IEditorInput#getName()
	 */
	public String getName() {
		return page.getName();
	}

	/**
	 * @see org.eclipse.ui.IEditorInput#getPersistable()
	 */
	public IPersistableElement getPersistable() {
		return null;
	}

	/**
	 * @see org.eclipse.ui.IEditorInput#getToolTipText()
	 */
	public String getToolTipText() {
		return page.getDescription();
	}

	/**
	 * @see org.eclipse.core.runtime.IAdaptable#getAdapter(java.lang.Class)
	 */
	public Object getAdapter(Class adapter) {
		if(adapter != null && Page.class.isAssignableFrom(adapter)) {
			return page;
		}
		
		return null;
	}

	public Page getWikiPage() {
		return page;
	}
	
	/**
	 *
	 * 
	 * @see java.lang.Object#equals(java.lang.Object)
	 */
	@Override
	public boolean equals(Object obj) {
		if (obj instanceof WikiPageEditorInput) {
			WikiPageEditorInput other = (WikiPageEditorInput) obj;
			try {
				CompareToBuilder comparer = new CompareToBuilder()
					.append(this.page.getName(), other.page.getName())
					.append(this.page.getServer().getServerDetails().getUrl().toString(), other.page.getServer().getServerDetails().getUrl().toString())
					.append(this.page.getServer().getServerDetails().getUsername(), other.page.getServer().getServerDetails().getUsername());
				return comparer.toComparison() == 0;
			} catch (NullPointerException e) { // FIXME
				// fall back to older implementation (works somehow in the happy cases)
				return this.storage.getName() == other.storage.getName();
			}
		}
		return false;
	}
}

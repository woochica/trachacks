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
 * @author Matteo Merli
 * 
 */
public class WikiEditorInput implements IStorageEditorInput {
	private Page page;
	private IStorage storage;

	public WikiEditorInput(Page page) {
		this.page = page;
		storage = new WikiEditorStorage(page);
	}

	public WikiEditorInput(Page page, boolean readonly) {
		this.page = page;
		storage = new WikiEditorStorage(page, readonly);
	}
	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.ui.IStorageEditorInput#getStorage()
	 */
	public IStorage getStorage() throws CoreException {
		return storage;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.ui.IEditorInput#exists()
	 */
	public boolean exists() {
		return true; //XXX
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.ui.IEditorInput#getImageDescriptor()
	 */
	public ImageDescriptor getImageDescriptor() {
		return Images.getDescriptor(Images.TRAC_16);
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.ui.IEditorInput#getName()
	 */
	public String getName() {
		return page.getName();// + ".tracwiki";
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.ui.IEditorInput#getPersistable()
	 */
	public IPersistableElement getPersistable() {
		return null;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.ui.IEditorInput#getToolTipText()
	 */
	public String getToolTipText() {
		return page.getDescription();
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see org.eclipse.core.runtime.IAdaptable#getAdapter(java.lang.Class)
	 */
	public Object getAdapter(Class adapter) {
		if (Page.class.equals(adapter))
			return page;

		// Log.info( "WikiEditorInput.getAdapter: " + adapter.toString() );
		/*
		 * if ( IFile.class.equals( adapter ) ) return storage; if (
		 * IResource.class.equals( adapter ) ) return storage;
		 */
		// Log.info( "Null" );
		return null;
	}

	public Page getWikiPage() {
		return page;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.lang.Object#equals(java.lang.Object)
	 */
	@Override
	public boolean equals(Object obj) {
		if (obj instanceof WikiEditorInput) {
			WikiEditorInput other = (WikiEditorInput) obj;
			try {
				CompareToBuilder comparer = new CompareToBuilder()
					.append(this.page.getName(), other.page.getName())
					.append(this.page.getServer().getServerDetails().getUrl().toString(), other.page.getServer().getServerDetails().getUrl().toString())
					.append(this.page.getServer().getServerDetails().getUsername(), other.page.getServer().getServerDetails().getUsername());
				return comparer.toComparison() == 0;
			} catch (NullPointerException e) {
				// fall back to older implementation (works somehow in the happy cases)
				return this.storage.getName() == other.storage.getName();
			}
		}
		return false;
	}

}

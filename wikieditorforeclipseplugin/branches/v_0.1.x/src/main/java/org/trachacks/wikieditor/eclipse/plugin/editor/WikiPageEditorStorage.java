package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import org.eclipse.core.resources.IStorage;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IPath;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

public class WikiPageEditorStorage implements IStorage {

	private Page page;

	/**
	 * @param page
	 */
	public WikiPageEditorStorage(Page page) {
		super();
		this.page = page;
	}
	
	public String getCharset() throws CoreException {
		return System.getProperty("file.encoding");
	}
	
	public InputStream getContents() throws CoreException {
		return  new ByteArrayInputStream(page.load().getContent().getBytes());
	}

	public IPath getFullPath() {
		return null;
	}

	public String getName() {
		return page.getName();
	}

	public boolean isReadOnly() {
		return false;
	}

	public Object getAdapter(Class adapter) {
		if(adapter != null && adapter.isInstance(Page.class)) {
			return page;
		}
		
		return null;
	}

}

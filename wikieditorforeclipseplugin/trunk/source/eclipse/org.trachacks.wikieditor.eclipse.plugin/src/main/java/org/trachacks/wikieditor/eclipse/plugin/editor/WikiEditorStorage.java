package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import org.eclipse.core.resources.IStorage;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IPath;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;

public class WikiEditorStorage implements IStorage {
	
	private boolean readonly = false;
	private Page page;
	private static final String Encoding = "utf-8";

	/**
	 * @param page
	 */
	public WikiEditorStorage(Page page) {
		super();
		this.page = page;
	}
	/**
	 * @param page
	 */
	public WikiEditorStorage(Page page, boolean readonly) {
		this(page);
		this.readonly = readonly;
	}

	public String getCharset() throws CoreException {
		return Encoding;
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
		return readonly;
	}

	public Object getAdapter(Class adapter) {
		return null;
	}

}

package org.trachacks.wikieditor.eclipse.plugin.editor;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.nio.charset.Charset;

import org.eclipse.core.resources.IStorage;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.core.runtime.IPath;
import org.eclipse.core.runtime.Status;
import org.trachacks.wikieditor.eclipse.plugin.Activator;
import org.trachacks.wikieditor.eclipse.plugin.Logger;
import org.trachacks.wikieditor.eclipse.plugin.model.Page;
import org.trachacks.wikieditor.model.exception.PageNotFoundException;

public class WikiEditorStorage implements IStorage {

	private static final String UTF8 = "utf-8";

	private boolean readonly = false;
	private String encoding;
	private Page page;
	

	/**
	 * @param page
	 */
	public WikiEditorStorage(Page page) {
		super();
		this.page = page;
		encoding = (Charset.isSupported(UTF8)) ? UTF8 : Charset.defaultCharset().displayName();
	}
	/**
	 * @param page
	 */
	public WikiEditorStorage(Page page, boolean readonly) {
		this(page);
		this.readonly = readonly;
	}

	public String getCharset() throws CoreException {
		return encoding;
	}

	public InputStream getContents() throws CoreException {
		try {
			return  new ByteArrayInputStream(page.load().getContent().getBytes(encoding));
		} catch (UnsupportedEncodingException e) {
			throw new CoreException(new Status(Status.ERROR, Activator.PLUGIN_ID, 
					"Default Charset is Not Supported: " + encoding, e));// This should not happen
		}
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

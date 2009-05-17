/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.comparation;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import org.eclipse.compare.IEditableContent;
import org.eclipse.compare.IStreamContentAccessor;
import org.eclipse.compare.ITypedElement;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.swt.graphics.Image;
import org.trachacks.wikieditor.eclipse.plugin.Images;
import org.trachacks.wikieditor.model.PageVersion;

/**
 * @author ivan
 *
 */
public class PageVersionInput implements ITypedElement,  IStreamContentAccessor {

	protected byte[] content;
	private String name;
	/**
	 * @param pageVersion
	 */
	public PageVersionInput(PageVersion pageVersion) {
		super();
		if(pageVersion != null) {
			name = pageVersion.getName();
			if(pageVersion.getContent() != null) {
				content = pageVersion.getContent().getBytes();
			}
		}
	}

	public InputStream getContents() throws CoreException {
		return new ByteArrayInputStream(content);
	}

	public Image getImage() {
		return Images.get(Images.TRAC_16);
	}

	public String getName() {
		return name;
	}

	public String getType() {
		return null;
	}


}

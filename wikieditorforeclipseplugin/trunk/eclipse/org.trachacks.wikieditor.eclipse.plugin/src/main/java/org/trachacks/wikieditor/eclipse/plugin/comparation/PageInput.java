/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.comparation;

import java.io.UnsupportedEncodingException;

import org.eclipse.compare.IEditableContent;
import org.eclipse.compare.ITypedElement;
import org.trachacks.wikieditor.model.PageVersion;

/**
 * @author ivan
 *
 */
public class PageInput extends PageVersionInput implements IEditableContent  {

	/**
	 * @param pageVersion
	 */
	public PageInput(PageVersion pageVersion) {
		super(pageVersion);
	}


	public boolean isEditable() {
		return true;
	}

	public ITypedElement replace(ITypedElement dest, ITypedElement src) {
		// TODO Auto-generated method stub
		return null;
	}

	public void setContent(byte[] newContent) {
		this.content = newContent;
	}
	
	public String getText() {
		try {
			return new String(content, "utf-8");
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
			return new String(content);
		}
	}

}

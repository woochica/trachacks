/**
 * 
 */
package org.trachacks.wikieditor.model;

/**
 * @author ivan
 *
 */
public class PageVersion extends PageInfo {

	private String content;
	private boolean edited = false;

	public String getContent() {
		return content;
	}

	public boolean isEdited() {
		return edited;
	}

	public void setEdited(boolean edited) {
		this.edited = edited;
	}

	public void setContent(String content) {
		this.content = content;
	}

}

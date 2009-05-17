/**
 * 
 */
package org.trachacks.wikieditor.disk.impl;

import org.w3c.dom.Document;

/**
 * @author ivan
 *
 */
public interface ISerializer {

	public void serialize(Document document, Object object);
}

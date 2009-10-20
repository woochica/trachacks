/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views.util;

import org.eclipse.swt.widgets.Composite;

/**
 * @author ivan
 *
 */
public class LabelTextArea extends LabelTextField{
	
	public LabelTextArea(Composite container, Object value, String key) {
		this(container, value, key, false);
	}
	
	public LabelTextArea(Composite container, Object value, String key, boolean required) {
		super(container, value, key, required);
		getText().setSize(getText().getSize().x, getText().getSize().y * 3);
	}
}

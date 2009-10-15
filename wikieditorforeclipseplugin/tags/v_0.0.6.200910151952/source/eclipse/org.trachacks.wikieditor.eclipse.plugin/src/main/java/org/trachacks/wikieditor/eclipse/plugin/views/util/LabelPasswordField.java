/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views.util;

import org.eclipse.swt.widgets.Composite;

/**
 * @author ivan
 *
 */
public class LabelPasswordField extends LabelTextField {

	public LabelPasswordField(Composite container, Object value, String key) {
		this(container, value, key, false);
	}

	/**
	 * @param container
	 * @param value
	 * @param key
	 * @param required
	 */
	public LabelPasswordField(Composite container, Object value, String key,	boolean required) {
		super(container, value, key, required);
		getText().setEchoChar((char) 0x2022);
	}

}

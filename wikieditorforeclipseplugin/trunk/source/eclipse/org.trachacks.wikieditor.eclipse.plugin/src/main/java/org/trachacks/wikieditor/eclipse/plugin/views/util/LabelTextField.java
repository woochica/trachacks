/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views.util;

import org.eclipse.swt.SWT;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Text;

/**
 * @author ivan
 *
 */
public class LabelTextField extends BaseLabelField {


	private Text text;


	public LabelTextField(Composite container, Object value, String key) {
		this(container, value, key, false);
	}
	
	public LabelTextField(Composite container, Object value, String key, boolean required) {
		super(container, value, key, required);
		String toolTip = Labels.getText(key + ".tooltip");
        text = new Text(container, SWT.BORDER | SWT.SINGLE);
        GridData gd = new GridData(GridData.FILL_HORIZONTAL);
        text.setLayoutData(gd);
        text.setToolTipText(toolTip);
        setValue(value);
	}

	/**
	 * @return
	 */
	@Override
	public String getValue() {
		return text.getText();
	}
	
	/**
	 * @param value
	 */
	public void setValue(String value) {
		if(value != null) {
			text.setText(value);
		}
		else {
			text.setText("");
		}
	}
	/**
	 * @param value
	 */
	@Override
	public void setValue(Object value) {
		if(value != null) {
			text.setText(value.toString());
		}
	}
	
	/**
	 * @return the text
	 */
	public Text getText() {
		return text;
	}
	/**
	 * @param text the text to set
	 */
	public void setText(Text text) {
		this.text = text;
	}

	@Override
	public void setFocus() {
		text.setFocus();
	}
	
}
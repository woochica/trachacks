/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views.util;

import org.apache.commons.lang.BooleanUtils;
import org.eclipse.swt.SWT;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;

/**
 * @author ivan
 *
 */
public class LabelCheckField extends BaseLabelField{

	private Button checkbox;

	public LabelCheckField(Composite container, Object value, String key) {
		this(container, value, key, false);
	}
	
	public LabelCheckField(Composite container, Object value, String key, boolean required) {
		super(container, value, key, required);
		
		String labelText = Labels.getText(key + ".label");
		String toolTip = Labels.getText(key + ".tooltip");

        checkbox = new Button( container, SWT.CHECK );
        GridData gd = new GridData(GridData.FILL_HORIZONTAL);
        checkbox.setLayoutData(gd);
        checkbox.setToolTipText(toolTip);
        setValue(value);
	}

	@Override
	public Object getValue() {
		return checkbox.getSelection();
	}
	
	public Boolean getValueAsBoolean() {
		return (Boolean) getValue();
	}

	@Override
	public void setFocus() {
		checkbox.setSelection(getValueAsBoolean());
	}

	@Override
	public void setValue(Object value) {
		Boolean isTrue = BooleanUtils.toBooleanObject(String.valueOf(value));
		checkbox.setSelection(isTrue);
	}


}


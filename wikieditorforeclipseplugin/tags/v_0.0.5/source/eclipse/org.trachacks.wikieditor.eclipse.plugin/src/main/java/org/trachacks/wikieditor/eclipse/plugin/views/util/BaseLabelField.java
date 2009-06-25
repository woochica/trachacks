/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views.util;

import org.eclipse.jface.fieldassist.ControlDecoration;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.MouseEvent;
import org.eclipse.swt.events.MouseListener;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Label;
import org.trachacks.wikieditor.eclipse.plugin.Images;

/**
 * @author ivan
 *
 */
public abstract class BaseLabelField {

	private Label label;
	private ErrorDecorator errorDecorator;
	private boolean valid;

	public BaseLabelField(Composite container, Object value, String key) {
		this(container, value, key, false);
	}
	
	public BaseLabelField(Composite container, Object value, String key, boolean required) {
		String labelText = Labels.getText(key + ".label");
		String toolTip = Labels.getText(key + ".tooltip");

        label = new Label(container, SWT.NULL);
        label.setText(labelText + (required? " (*)" : " ") + ":");
        label.setToolTipText(toolTip);
        label.setLayoutData(new GridData(SWT.RIGHT, SWT.CENTER, false, false, 1, 1));
        errorDecorator = new ErrorDecorator(label);
        
        label.addMouseListener(new MouseListener() {
			public void mouseDoubleClick(MouseEvent e) {}
			public void mouseUp(MouseEvent e) {}
			public void mouseDown(MouseEvent e) {
				if(e.button == 1) {
					setFocus();
				}
			}
        });

	}

	public abstract void setFocus();
	public abstract Object getValue();
	public abstract void setValue(Object value);
	
	/**
	 * @return the label
	 */
	public Label getLabel() {
		return label;
	}
	/**
	 * @param label the label to set
	 */
	public void setLabel(Label label) {
		this.label = label;
	}

	/**
	 * @return the valid
	 */
	public boolean isValid() {
		return valid;
	}

	/**
	 * @param valid the valid to set
	 */
	public void setValid() {
		this.valid = true;
		errorDecorator.setValid();
	}
	
	public void setInvalid(String description) {
		this.valid = false;
		errorDecorator.setInvalid(description);
	}
	
}
class ErrorDecorator extends  ControlDecoration {

	public ErrorDecorator(Label label) {
		super(label, SWT.LEFT | SWT.CENTER);
		setMarginWidth(4);
		setImage(Images.get(Images.ERROR));		
		setValid();
	}
	
	public void setValid() {
		hide();
		setDescriptionText("");
	}
	
	public void setInvalid(String description) {
		show();
		setDescriptionText(description);
	}
	
}

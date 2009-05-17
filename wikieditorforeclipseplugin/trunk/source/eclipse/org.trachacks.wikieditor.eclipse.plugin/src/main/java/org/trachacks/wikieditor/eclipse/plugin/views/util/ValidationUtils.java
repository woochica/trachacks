/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.views.util;


import java.net.MalformedURLException;
import java.net.URL;

import org.apache.commons.lang.StringUtils;

/**
 * @author ivan
 *
 */
public class ValidationUtils {

	
	public static boolean validateRequired(LabelTextField labelTextField) {
		markValid(labelTextField);
		String text = labelTextField.getValue();
		if(StringUtils.isBlank(text)) {
			markAsInvalid(labelTextField, Labels.getText("validate.required"));
			return false;
		}
		return true;
	}
	
	public static boolean validateURL(LabelTextField labelTextField) {
		markValid(labelTextField);
		String text = labelTextField.getValue();
		if(StringUtils.isNotBlank(text)) {
			try {
				new URL(text);
			} catch (MalformedURLException e) {
				markAsInvalid(labelTextField, Labels.getText("validate.URL"));
				return false;
			}
		}
		return true;
	}
	
	private static void markValid(LabelTextField labelTextField) {
		labelTextField.setValid();
	}
	
	private static void markAsInvalid(LabelTextField labelTextField, String description) {
		labelTextField.setInvalid(description);
	}
}

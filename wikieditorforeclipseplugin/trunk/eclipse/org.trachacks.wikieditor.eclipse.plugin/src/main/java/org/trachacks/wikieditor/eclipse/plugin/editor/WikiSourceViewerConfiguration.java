/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.editor;

import org.eclipse.jface.preference.IPreferenceStore;
import org.eclipse.mylyn.internal.wikitext.ui.editor.MarkupSourceViewerConfiguration;

/**
 * @author ivan
 *
 */
public class WikiSourceViewerConfiguration extends 	MarkupSourceViewerConfiguration {

	public WikiSourceViewerConfiguration(IPreferenceStore preferenceStore) {
		super(preferenceStore);
	}
	
}

/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.model;

import org.trachacks.wikieditor.eclipse.plugin.model.util.IModelChangeListener;
import org.trachacks.wikieditor.eclipse.plugin.model.util.WeakCollection;


/**
 * @author Matteo Merli
 * 
 */
public class AbstractBaseObject {
	private WeakCollection<IModelChangeListener> listeners;

	public void addListener(IModelChangeListener listener) {
		if (listeners == null)
			listeners = new WeakCollection<IModelChangeListener>();

		listeners.add(listener);
	}

	public void removeListener(IModelChangeListener listener) {
		if (listeners != null) {
			listeners.remove(listener);
		}
	}

	protected void notifyChanged() {
		if (listeners == null)
			return;

		for (IModelChangeListener listener : listeners) {
			if (listener != null)
				listener.tracResourceModified(this);
		}
	}
}

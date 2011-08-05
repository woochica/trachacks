/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin;

import org.eclipse.core.runtime.Status;

/**
 * @author ivan
 *
 */
public class Logger {

	
	public static void error(String message, Throwable exception) {
		Activator.getDefault().getLog()
			.log(new Status(Status.ERROR, Activator.PLUGIN_ID, message, exception)); 
	}

	public static void warning(String message, Throwable exception) {
		Activator.getDefault().getLog()
			.log(new Status(Status.WARNING, Activator.PLUGIN_ID, message, exception)); 
	}

	public static void info(String message, Throwable exception) {
		Activator.getDefault().getLog()
			.log(new Status(Status.INFO, Activator.PLUGIN_ID, message, exception)); 
	}

}

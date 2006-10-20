/**
 * Copyright 2006 Aldrin Leal, aldrin at leal dot eng dot bee ar
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); 
 * you may not use this file except in compliance with the License. 
 * You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software 
 * distributed under the License is distributed on an "AS IS" BASIS, 
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
 * See the License for the specific language governing permissions and 
 * limitations under the License.
 */
package br.eng.leal.trac;

import java.io.File;

/**
 * Tracifier is an utility class for some special operations
 *
 * TODO: BROKEN
 * TODO: Needs a UnitTest
 * 
 * @author Aldrin Leal
 */
public class Tracifier {
	/**
	 * Given a classname, searches for, trying to find an suitable location,
	 * returning a Wiki Link in the form
	 * "[source:path/to/java/sources/Source.java Source]"
	 * 
	 * @param className
	 *            Class to find the source code to represent
	 * @return null if the resource name wasn't found, otherwise the link, as
	 *         specified above
	 * 
	 */
	public static String getLinkFonteClasse(String className) {
		Class clazz = null;

		try {
			clazz = Class.forName(className);
		} catch (Exception exc) {
			return className;
		}

		StringBuilder nomeBuilder = new StringBuilder("[source:/trunk/");

		nomeBuilder.append("main/src/");

		int offset1 = nomeBuilder.length();

		nomeBuilder.append(className.replaceAll("\\$.*$", "").replaceAll("\\.",
				"/"));
		nomeBuilder.append(".java");

//		if (new File(StringUtils.join(new String[] { "main/src/java",
//				nomeBuilder.substring(offset1) }, '/')).exists()) {
//			nomeBuilder.insert(offset1, "java/");
//
//			nomeBuilder.append(" ");
//			nomeBuilder.append(clazz.getSimpleName());
//			nomeBuilder.append("]");
//
//			return nomeBuilder.toString();
//		} else if (new File(StringUtils.join(new String[] { "main/src/test",
//				nomeBuilder.substring(offset1) }, '/')).exists()) {
//			nomeBuilder.insert(offset1, "test/");
//			nomeBuilder.append(clazz.getSimpleName());
//			nomeBuilder.append("]");
//
//			return nomeBuilder.toString();
//		}

		return className;
	}
}

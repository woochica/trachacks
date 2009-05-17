package org.trachacks.wikieditor.eclipse.plugin.editor.model;

/*******************************************************************************
 * Copyright (c) 2000 IBM Corporation and others.
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v10.html
 *
 * Contributors:
 *     IBM Corporation - initial API and implementation
 *******************************************************************************/

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;


import org.eclipse.jface.text.Position;

public class WikiSection {
	protected final static List<WikiSection> NO_CHILDREN = Collections.unmodifiableList(new ArrayList<WikiSection>());

	private WikiSection parent;

	private String name;

	private int headerLevel;

	private Position position;

	protected List<WikiSection> children;

	WikiSection(String name, int level, Position position) {
		this.name = name;
		this.headerLevel = level;
		this.position = position;
		children = null;
	}

	public List<WikiSection> getChildren() {
		return children == null ? NO_CHILDREN : children;
	}

	public String getName() {
		return name;
	}

	public int getOffset() {
		return position == null ? -1 : position.offset;
	}

	public int getLength() {
		return position == null ? -1 : position.length;
	}

	/**
	 * @param o
	 * @return
	 */
	public boolean add(WikiSection o) {
		if (children == null)
			children = new ArrayList<WikiSection>();
		return children.add(o);
	}

	/**
	 * @param index
	 * @return
	 */
	public WikiSection get(int index) {
		return children.get(index);
	}

	/**
	 * @return
	 */
	public int size() {
		return children.size();
	}

	/**
	 * @return Returns the headerLevel.
	 */
	public int getHeaderLevel() {
		return headerLevel;
	}

	/**
	 * @param fheaderLevel
	 *            The headerLevel to set.
	 */
	public void setHeaderLevel(int headerLevel) {
		this.headerLevel = headerLevel;
	}

	/**
	 * @return Returns the parent.
	 */
	public WikiSection getParent() {
		return parent;
	}

	/**
	 * @param parent
	 *            The parent to set.
	 */
	public void setParent(WikiSection parent) {
		this.parent = parent;
	}

	/**
	 * Look for the section preceding the cursor.
	 * 
	 * @param offset
	 * @param margin
	 * @return
	 */
	public WikiSection find(int offset, int margin, WikiSection found) {
		if (margin == -1)
			margin = Integer.MAX_VALUE;

//		Log.info("Checking: " + name + " - " + this.position.getOffset());
//		Log.info("Current Margin: " + margin);
//		if (found != null)
//			Log.info("Temp: " + found.getName());

		int diff = offset - this.position.getOffset();
//		Log.info("Diff: " + diff);

		if (diff >= 0 && diff < margin) {
			found = this;
			margin = diff;
		}

		for (WikiSection child : children) {
			found = child.find(offset, margin, found);
		}

		return found;
	}
}

/**
 * 
 */
package org.trachacks.wikieditor.eclipse.plugin.model.util;

import java.lang.ref.ReferenceQueue;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;
import java.util.NoSuchElementException;

/**
 * WeakCollection is a container of weakly reachable items, that means that
 * being the item in this collection don't prevent them from being garbage
 * collected.
 * 
 * @author Matteo Merli
 * 
 */
public class WeakCollection<T> implements Collection<T> {
	private ArrayList<WeakReference<T>> data;

	/**
	 * Reference queue for cleared WeakEntries
	 */
	private final ReferenceQueue<T> queue = new ReferenceQueue<T>();

	public WeakCollection() {
		data = new ArrayList<WeakReference<T>>();
	}

	public WeakCollection(int size) {
		data = new ArrayList<WeakReference<T>>(size);
	}

	public WeakCollection(Collection<T> collection) {
		data = new ArrayList<WeakReference<T>>(collection.size());

		for (T item : collection) {
			data.add(new WeakReference<T>(item, queue));
		}
	}

	/**
	 * @param o
	 * @return
	 * @see java.util.Collection#add(java.lang.Object)
	 */
	public boolean add(T o) {
		return data.add(new WeakReference<T>(o, queue));
	}

	/**
	 * @param c
	 * @return
	 * @see java.util.Collection#addAll(java.util.Collection)
	 */
	public boolean addAll(Collection<? extends T> c) {
		Collection<WeakReference<T>> list = new ArrayList<WeakReference<T>>(c
				.size());
		for (T element : c)
			list.add(new WeakReference<T>(element));

		return data.addAll(list);
	}

	/**
	 * 
	 * @see java.util.Collection#clear()
	 */
	public void clear() {
		removeStaleEntries();
		data.clear();
	}

	/**
	 * @param o
	 * @return
	 * @see java.util.Collection#contains(java.lang.Object)
	 */
	public boolean contains(Object o) {
		return data.contains(o);
	}

	/**
	 * @param c
	 * @return
	 * @see java.util.Collection#containsAll(java.util.Collection)
	 */
	public boolean containsAll(Collection<?> c) {
		return data.containsAll(c);
	}

	/**
	 * @param o
	 * @return
	 * @see java.util.Collection#equals(java.lang.Object)
	 */
	public boolean equals(Object o) {
		return this == o;
	}

	/**
	 * @return
	 * @see java.util.Collection#hashCode()
	 */
	public int hashCode() {
		return data.hashCode();
	}

	/**
	 * @return
	 * @see java.util.Collection#isEmpty()
	 */
	public boolean isEmpty() {
		return data.isEmpty();
	}

	/**
	 * @return
	 * @see java.util.Collection#iterator()
	 */
	public Iterator<T> iterator() {
		return new WeakIterator();
	}

	/**
	 * @param o
	 * @return
	 * @see java.util.Collection#remove(java.lang.Object)
	 */
	public boolean remove(Object o) {
		int idx = indexOf(o);
		if (idx < 0)
			return false;

		data.remove(idx);
		return true;
	}

	/**
	 * @param c
	 * @return
	 * @see java.util.Collection#removeAll(java.util.Collection)
	 */
	public boolean removeAll(Collection<?> c) {
		removeStaleEntries();
		for (Object o : c) {
			if (!remove(o))
				return false;
		}
		return true;
	}

	/**
	 * @param c
	 * @return
	 * @see java.util.Collection#retainAll(java.util.Collection)
	 */
	public boolean retainAll(Collection<?> c) {
		return data.retainAll(c);
	}

	/**
	 * @return
	 * @see java.util.Collection#size()
	 */
	public int size() {
		removeStaleEntries();
		return data.size();
	}

	/**
	 * @return
	 * @see java.util.Collection#toArray()
	 */
	public Object[] toArray() {
		Object[] array = new Object[data.size()];
		return toArray(array);
	}

	/**
	 * @param <E>
	 * @param a
	 * @return
	 * @see java.util.Collection#toArray(E[])
	 */
	@SuppressWarnings("unchecked")
	public <E> E[] toArray(E[] a) {
		Object[] array;
		if (a.length >= data.size())
			array = a;
		else
			array = new Object[data.size()];

		int i = 0;
		for (Object item : data)
			array[i++] = ((WeakReference<T>) item).get();

		return (E[]) array;
	}

	private int indexOf(Object item) {
		int size = data.size();
		if (item == null) {
			for (int i = 0; i < size; i++)
				if (data.get(i).get() == null)
					return i;
		} else {
			for (int i = 0; i < size; i++)
				if (item.equals(data.get(i).get()))
					return i;
		}
		return -1;
	}

	private void removeStaleEntries() {
		Object entry;

		while ((entry = queue.poll()) != null) {
			data.remove(entry);
		}

	}

	private class WeakIterator implements Iterator<T> {

		private int cursor;

		public WeakIterator() {
			cursor = -1;
		}

		public boolean hasNext() {
			return cursor < (data.size() - 1);
		}

		public T next() {
			if (!hasNext())
				throw new NoSuchElementException();

			return data.get(++cursor).get();
		}

		public void remove() {
			if (cursor < 0 || cursor >= data.size())
				throw new IllegalStateException();

			data.remove(cursor);
		}

	}

}

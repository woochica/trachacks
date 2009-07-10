/**
 * 
 */
package org.trachacks.wikieditor.disk.impl;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

/**
 * @author ivan
 *
 */
public class SerializationUtils {

	public static void serialize(File file, Object object, ISerializer serializer) {
		FileOutputStream stream= null;
		try {
			Document doc = getDocument();

			serializer.serialize(doc, object);

			if (!file.exists()) {
				file.createNewFile();
			}
			stream = new FileOutputStream(file);
			stream.write(documentAsBytes(doc));
			
		} catch (IOException e) {
			e.printStackTrace(); // FIXME
		} catch (ParserConfigurationException e) {
			e.printStackTrace(); // FIXME
		} catch (TransformerException e) {
			e.printStackTrace(); // FIXME
		} finally {
			if (stream != null) {
				try {
					stream.close();
				} catch (IOException ignored) {}
			}
        }
		return;
	}
	
	public static Element loadRootElement(File file) {
		if (file.exists()) {
			try {
				InputStream stream = new FileInputStream(file);
				DocumentBuilder parser = DocumentBuilderFactory.newInstance().newDocumentBuilder();
				parser.setErrorHandler(new DefaultHandler());
				return parser.parse(new InputSource(stream)).getDocumentElement();
				
			} catch (IOException e) {
				e.printStackTrace(); // FIXME
			} catch (ParserConfigurationException e) {
				e.printStackTrace(); // FIXME
			} catch (SAXException e) {
				e.printStackTrace(); // FIXME
			}
		} 

		return null;
	}
	
	
	/**
	 * 
	 * @return
	 * @throws ParserConfigurationException
	 */
	private static Document getDocument() throws ParserConfigurationException {
		DocumentBuilderFactory dfactory= DocumentBuilderFactory.newInstance();
		DocumentBuilder docBuilder= dfactory.newDocumentBuilder();
		Document doc= docBuilder.newDocument();
		return doc;
	}
	
	/**
	 * 
	 * @param doc
	 * @return
	 * @throws IOException
	 * @throws TransformerException
	 */
	private static byte[] documentAsBytes(Document doc) throws IOException, TransformerException {
		ByteArrayOutputStream s= new ByteArrayOutputStream();
		
		TransformerFactory factory= TransformerFactory.newInstance();
		Transformer transformer= factory.newTransformer();
		transformer.setOutputProperty(OutputKeys.METHOD, "xml"); //$NON-NLS-1$
		transformer.setOutputProperty(OutputKeys.INDENT, "yes"); //$NON-NLS-1$
		
		DOMSource source= new DOMSource(doc);
		StreamResult outputTarget= new StreamResult(s);
		transformer.transform(source, outputTarget);
		
		return s.toByteArray();
	}
}

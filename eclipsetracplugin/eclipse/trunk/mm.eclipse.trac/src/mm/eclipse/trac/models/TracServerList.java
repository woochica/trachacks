/**
 * 
 */
package mm.eclipse.trac.models;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.Log;

import org.eclipse.core.runtime.IPath;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

/**
 * @author Matteo Merli
 * 
 */
public class TracServerList extends ModelBase implements Iterable<TracServer>
{
    private List<TracServer>    servers;
    
    public List<TracServer> getServers()
    {
        return servers;
    }
    
    public void addServer( TracServer server )
    {
        servers.add( server );
        notifyChanged();
    }
    
    public void removeServer( TracServer server )
    {
        servers.remove( server );
        notifyChanged();
    }
    
    private TracServerList()
    {
    	servers = new ArrayList<TracServer>();
        loadPreferences();
        
    }
    
    private void loadPreferences()
    {
		IPath libPath = Activator.getDefault().getStateLocation();
		libPath = libPath.append("servers.xml"); //$NON-NLS-1$
		File file = libPath.toFile();
		if (file.exists()) {
			try {
				InputStream stream = new FileInputStream(file);
				DocumentBuilder parser = DocumentBuilderFactory.newInstance().newDocumentBuilder();
				parser.setErrorHandler(new DefaultHandler());
				Element root = parser.parse(new InputSource(stream)).getDocumentElement();
				if(!root.getNodeName().equals("serverInfos")) { //$NON-NLS-1$
					return;
				}
				
				NodeList list = root.getChildNodes();
				int length = list.getLength();
				for (int i = 0; i < length; ++i) {
					Node node = list.item(i);
					short type = node.getNodeType();
					if (type == Node.ELEMENT_NODE) {
						Element element = (Element) node;
						String nodeName = element.getNodeName();
						if (nodeName.equalsIgnoreCase("server")) { //$NON-NLS-1$
							String name = element.getAttribute("name"); //$NON-NLS-1$
							String url = element.getAttribute("url"); //$NON-NLS-1$
							String username = element.getAttribute("username"); //$NON-NLS-1$
							String password = element.getAttribute("password"); //$NON-NLS-1$
							String anonymous = element.getAttribute("anonymous"); //$NON-NLS-1$
							TracServer server = new TracServer(name,new URL(url),username,password,Boolean.parseBoolean(anonymous));
							server.connect();
							servers.add(server);
						}
					}
				}
				
			} catch (IOException e) {
				Log.error("Error is occured.", e);
			} catch (ParserConfigurationException e) {
				Log.error("Error is occured.", e);
			} catch (SAXException e) {
				Log.error("Error is occured.", e);
			}
		}

    	Activator.getDefault().getStateLocation();
    }
    
	/*
     * (non-Javadoc)
     * 
     * @see java.lang.Iterable#iterator()
     */
    public Iterator<TracServer> iterator()
    {
        if ( servers == null ) return null;
        
        return servers.iterator();
    }
    
    public static TracServerList getInstance()
    {
        if ( instance == null ) instance = new TracServerList();
        
        return instance;
    }
    
    private static TracServerList instance;
    
    @Override
    protected void notifyChanged() {
    	try {
			savePreferences();
		} catch (ParserConfigurationException e) {
		} catch (IOException e) {
		} catch (TransformerException e) {
		}
    	super.notifyChanged();
    }
    private void savePreferences() throws ParserConfigurationException, IOException, TransformerException
    {
		FileOutputStream stream= null;
		try {
			String xml = getServerInfoAsXML();
			IPath libPath = Activator.getDefault().getStateLocation();
			libPath = libPath.append("servers.xml");
			File file = libPath.toFile();
			if (!file.exists()) {
				file.createNewFile();
			}
			stream = new FileOutputStream(file);
			stream.write(xml.getBytes("UTF8")); //$NON-NLS-1$
		} catch (IOException e) {
			Log.error("exception is occured.",e);
		} catch (ParserConfigurationException e) {
			Log.error("exception is occured.",e);
		} catch (TransformerException e) {
			Log.error("exception is occured.",e);
		} finally {
			if (stream != null) {
				try {
					stream.close();
				} catch (IOException e1) {
				}
			}
        }
    }
    
    private String getServerInfoAsXML() throws ParserConfigurationException, IOException, TransformerException {
		Document doc = getDocument();
		Element config = doc.createElement("serverInfos");    //$NON-NLS-1$
		doc.appendChild(config);
		for(TracServer server : TracServerList.getInstance()){
			Element serverElement = doc.createElement("server");    //$NON-NLS-1$
			serverElement.setAttribute("name", server.getName()); //$NON-NLS-1$
			serverElement.setAttribute("url", server.getUrl().toString()); //$NON-NLS-1$
			serverElement.setAttribute("username", server.getUsername()); //$NON-NLS-1$
			serverElement.setAttribute("password", server.getPassword()); //$NON-NLS-1$
			serverElement.setAttribute("anonymous", Boolean.toString(server.isAnonymous())); //$NON-NLS-1$
			config.appendChild(serverElement);
		}
		return serializeDocument(doc);
	}
    
	private Document getDocument() throws ParserConfigurationException {
		DocumentBuilderFactory dfactory= DocumentBuilderFactory.newInstance();
		DocumentBuilder docBuilder= dfactory.newDocumentBuilder();
		Document doc= docBuilder.newDocument();
		return doc;
	}
	
	private String serializeDocument(Document doc) throws IOException, TransformerException {
		ByteArrayOutputStream s= new ByteArrayOutputStream();
		
		TransformerFactory factory= TransformerFactory.newInstance();
		Transformer transformer= factory.newTransformer();
		transformer.setOutputProperty(OutputKeys.METHOD, "xml"); //$NON-NLS-1$
		transformer.setOutputProperty(OutputKeys.INDENT, "yes"); //$NON-NLS-1$
		
		DOMSource source= new DOMSource(doc);
		StreamResult outputTarget= new StreamResult(s);
		transformer.transform(source, outputTarget);
		
		return s.toString("UTF8"); //$NON-NLS-1$			
	}

}

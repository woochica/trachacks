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
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PipedInputStream;
import java.io.PipedOutputStream;
import java.util.Properties;

import com.jcraft.jsch.ChannelExec;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;

/**
 * Representa um OutputStream que salva em uma página Wiki para o Trac
 * 
 * @author aldrin
 */
public class WikiPageOutputStream extends OutputStream {
	/**
	 * Just in case one forgets remote TRAC_DB PATH
	 */
	private static final IllegalArgumentException TRACDB_MISSING_ILLEGAL_ARGUMENT_EXCEPTION = new IllegalArgumentException(
			"You must supply an remote TRAC_DB path!");

	/**
	 * But perhaps someone else also forgets to supply a valid Path to a Key
	 * File
	 */
	private static final RuntimeException KEYFILE_MISSING_ILLEGAL_ARGUMENT_EXCEPTION = new IllegalArgumentException(
			"Keyfile is mandatory!");

	/**
	 * Or someone override the properties, thus disabling its use
	 */
	private static final RuntimeException DISABLED_EXCEPTION = new IllegalArgumentException(
			"WikiPageOutputStream class is Disabled for Construction!");

	/**
	 * PROPERTY KEY CONSTANT FOR: Remote Trac User
	 */
	public static final String REMOTE_TRAC_USER = "remote.trac.user";

	/**
	 * PROPERTY KEY CONSTANT FOR: Remote Trac Host
	 */
	public static final String REMOTE_TRAC_HOST = "remote.trac.host";

	/**
	 * PROPERTY KEY CONSTANT FOR: Remote Path to Your trac-admin Binary
	 */
	private static final String REMOTE_TRAC_ADMIN = "remote.trac.trac-admin.path";

	/**
	 * PROPERTY KEY CONSTANT FOR: Remote Path to Your Remote TRAC_DB
	 */
	private static final String REMOTE_TRAC_DB = "remote.trac.db.path";

	/**
	 * PROPERTY KEY CONSTANT FOR: Remote SSH Port (defaults to: 22)
	 */
	private static final String REMOTE_TRAC_PORT = "remote.trac.host.port";

	/**
	 * PROPERTY KEY CONSTANT FOR: Remote Temp Path for Wiki Page
	 * Storage(defaults to: "/tmp")
	 */
	private static final String REMOTE_TMP_PATH = "remote.trac.tmp.path";

	/**
	 * PROPERTY KEY CONSTANT FOR: Path to Remote Host User [RD]SA Auth Key
	 */
	private static final String REMOTE_TRAC_USER_KEY = "remote.trac.user.key";

	/**
	 * PROPERTY KEY FOR: OVERRIDE WikiPageOutputStream, thus disabling
	 * construction;
	 */
	private static final String WIKIOUTPUTSTREAM_DISABLED = "wiki.disabled";

	/**
	 * Underlying OutputStream de jure
	 */
	private OutputStream outputStream;

	/**
	 * JSch Connection Factory
	 */
	private JSch jschFactory;

	/**
	 * JSch Session
	 */
	private Session jschSession;

	/**
	 * JSch ChannelExec
	 */
	private ChannelExec jschChannel;

	/**
	 * Remote stdout, as an OutputStream (where jschChannel writes to)
	 */
	private OutputStream remoteOutputStream;

	/**
	 * Remote stderr, as an OutputStream (where jschChannel also writes to)
	 */
	private OutputStream remoteErrorStream;

	/**
	 * Remote stdin, as an InputStream (jschChannel reads from)
	 */
	private PipedInputStream remoteInputStream;

	/**
	 * Local View from remoteOutputStream (where we will read from)
	 * 
	 * @see WikiPageOutputStream#remoteOutputStream
	 */
	private PipedInputStream remoteOutputInputStream;

	/**
	 * Local View from remoteErrorStream (where we will read from)
	 * 
	 * @see WikiPageOutputStream#remoteErrorStream
	 */
	private PipedInputStream remoteErrorInputStream;

	/**
	 * Default Constructor, which: <br/><br/>
	 * 
	 * <ul>
	 * <li>Loads Properties from System-wide Scope</li>
	 * <li>Locates trac.properties. If found, override the System-wide ones</li>
	 * <li>Validates</li>
	 * <li>And finally, setups an SSH Connection, invoking
	 * 
	 * <pre>
	 *            cat &gt; tmpfilename &amp;&amp; trac-admin TRACDB wiki import page tmpFile &amp;&amp; rm -f tmpfilename
	 * </pre>
	 * 
	 * </li>
	 * 
	 * @param page
	 *            Wiki Page to Create/Update
	 */
	public WikiPageOutputStream(String page) throws JSchException, IOException {
		Properties props = new Properties();

		InputStream propertiesInputStream = this.getClass().getClassLoader()
				.getResourceAsStream("trac.properties");

		if (null != propertiesInputStream)
			props.load(propertiesInputStream);

		init(page, props);
	}

	/**
	 * Default Constructor, suitable for general Unix usage
	 * 
	 * @param page
	 *            Wiki Page to Create/Update
	 * @param properties
	 *            Properties
	 * @throws IOException
	 *             I/O / Network Failure
	 * @throws JSchException
	 *             Network / SSH Protocol Failure
	 */
	public WikiPageOutputStream(String page, Properties properties)
			throws JSchException, IOException {
		init(page, properties);
	}

	/**
	 * Property Setup, first Stage: Property Care, Load and Handling
	 * 
	 * @param page
	 *            Page to Create/Update
	 * @param properties
	 *            Properties to Read From
	 * @throws IOException
	 *             I/O / Network Failure
	 * @throws JSchException
	 *             Network / SSH Protocol Failure
	 */
	private void init(String page, Properties properties) throws JSchException,
			IOException {
		String remoteUser = getProperty(properties, REMOTE_TRAC_USER);
		String remoteHost = getProperty(properties, REMOTE_TRAC_HOST);
		int remotePort = Integer.parseInt(getProperty(properties,
				REMOTE_TRAC_PORT, "22"));
		String tracDb = getProperty(properties, REMOTE_TRAC_DB,
				TRACDB_MISSING_ILLEGAL_ARGUMENT_EXCEPTION);
		String tracAdmin = getProperty(properties, REMOTE_TRAC_ADMIN,
				"trac-admin");
		String tmpPrefix = getProperty(properties, REMOTE_TMP_PATH, "/tmp");
		String keyFile = getProperty(properties, REMOTE_TRAC_USER_KEY,
				KEYFILE_MISSING_ILLEGAL_ARGUMENT_EXCEPTION);
		Boolean disabled = Boolean.parseBoolean(getProperty(properties,
				WIKIOUTPUTSTREAM_DISABLED, "false"));

		if (null != disabled)
			if (disabled.booleanValue())
				throw DISABLED_EXCEPTION;

		init(page, remoteUser, remoteHost, remotePort, tracDb, tracAdmin,
				tmpPrefix, new File(keyFile));
	}

	/**
	 * *THE REAL CTOR*
	 * 
	 * @param page
	 *            Page to Create/Update
	 * @param user
	 *            Remote User, permission-wise to invoke trac-admin and handle
	 *            TRAC_DB
	 * @param host
	 *            Remote Host
	 * @param port
	 *            Remote Port
	 * @param tracDb
	 *            Remote Path to TracDB
	 * @param tracAdmin
	 *            Remote Path to trac-admin
	 * @param remoteTmpPrefix
	 *            Remote Path to Temporary File Creation
	 * @param keyFile
	 *            SSH KeyFile for
	 * 
	 * <pre>
	 *        Remote User@Remote Host:Remote Port
	 * </pre>
	 * 
	 * @throws IOException
	 *             I/O / Network Failure
	 * @throws JSchException
	 *             Network / SSH Protocol Failure
	 */
	public WikiPageOutputStream(String page, String user, String host,
			int port, String tracDb, String tracAdmin, String remoteTmpPrefix,
			File keyFile) throws JSchException, IOException {
		init(page, user, host, port, tracDb, tracAdmin, remoteTmpPrefix,
				keyFile);
	}

	/**
	 * Connection Setup
	 * 
	 * @param page
	 *            Nome da Página Wiki
	 * @param page
	 *            Page to Create/Update
	 * @param user
	 *            Remote User, permission-wise to invoke trac-admin and handle
	 *            TRAC_DB
	 * @param host
	 *            Remote Host
	 * @param port
	 *            Remote Port
	 * @param tracDb
	 *            Remote Path to TracDB
	 * @param tracAdmin
	 *            Remote Path to trac-admin
	 * @param remoteTmpPrefix
	 *            Remote Path to Temporary File Creation
	 * @param keyFile
	 *            SSH KeyFile for
	 * 
	 * <pre>
	 *        Remote User@Remote Host:Remote Port
	 * </pre>
	 * 
	 * @throws IOException
	 *             I/O / Network Failure
	 * @throws JSchException
	 *             Network / SSH Protocol Failure
	 */
	private void init(String page, String user, String host, int port,
			String tracDb, String tracAdmin, String remoteTmpPrefix,
			File keyFile) throws JSchException, IOException {
		/*
		 * Builds the Remote WikiPage Temporary File Path
		 */

		String remoteTmpFile = remoteTmpPrefix + "/" + page + "."
				+ System.identityHashCode(this) + "."
				+ System.currentTimeMillis() + ".tmp";

		/*
		 * Next, Constructs the remote command to be issued for Wiki Page
		 * Loading
		 */
		StringBuilder remoteCommand = new StringBuilder();

		remoteCommand.append("/bin/cat > ");
		remoteCommand.append(remoteTmpFile);
		remoteCommand.append(" && ");
		remoteCommand.append(tracAdmin);
		remoteCommand.append(" ");
		remoteCommand.append(tracDb);
		remoteCommand.append(" wiki import ");
		remoteCommand.append(page);
		remoteCommand.append(" ");
		remoteCommand.append(remoteTmpFile);
		remoteCommand.append(" && /bin/rm -f ");
		remoteCommand.append(remoteTmpFile);

		/*
		 * JSCh Setup, Part One: JSch Key Management for known_hosts
		 */
		this.jschFactory = new JSch();
		this.jschFactory.setKnownHosts(System.getProperty("user.home")
				+ File.separatorChar + ".ssh" + File.separatorChar
				+ "known_hosts");
		this.jschFactory.addIdentity(keyFile.getAbsolutePath());

		/*
		 * Part Two: Session Instantiation / Connection
		 */
		this.jschSession = jschFactory.getSession(user, host, port);
		this.jschSession.connect();

		/*
		 * Part Three: I/O Channels Setup
		 */
		this.remoteInputStream = new PipedInputStream();
		this.outputStream = new PipedOutputStream(remoteInputStream);

		this.remoteOutputInputStream = new PipedInputStream();
		this.remoteOutputStream = new PipedOutputStream(
				this.remoteOutputInputStream);

		this.remoteErrorInputStream = new PipedInputStream();

		this.remoteErrorStream = new PipedOutputStream(
				this.remoteErrorInputStream);

		/*
		 * Part Four: Channel Setup
		 */
		this.jschChannel = (ChannelExec) this.jschSession.openChannel("exec");

		this.jschChannel.setCommand(remoteCommand.toString());

		this.jschChannel.setInputStream(this.remoteInputStream);
		this.jschChannel.setOutputStream(this.remoteOutputStream);
		this.jschChannel.setErrStream(this.remoteErrorStream);

		/*
		 * Part Five: Channel Establishment
		 */
		this.jschChannel.connect();
	}

	/**
	 * Property Getter, Mandatory Property
	 * 
	 * @param properties
	 *            Properties to Load From
	 * @param propertyName
	 *            Property Name
	 * @param exception
	 *            RuntimeException To Be Thrown
	 * @return Property Value
	 */
	private String getProperty(Properties properties, String propertyName,
			RuntimeException exception) {
		String value = getProperty(properties, propertyName);

		if (null == value || 0 == value.length())
			throw exception;

		return value;
	}

	/**
	 * Property Getter, Optional Property
	 * 
	 * @param properties
	 *            Properties to Load From
	 * @param propertyName
	 *            Property Name
	 * @param defaultValue
	 *            Default Value
	 * @return defaultValue in worst case, best case the system-or-property
	 *         supplied to all the others
	 */
	private String getProperty(Properties properties, String propertyName,
			String defaultValue) {
		String value = defaultValue;

		if (null != properties) {
			if (null != properties.getProperty(propertyName))
				return properties.getProperty(propertyName);
		} else if (null != System.getProperty(propertyName)) {
			return System.getProperty(propertyName);
		}

		return value;
	}

	/**
	 * Property Getter, Generic
	 * 
	 * @param properties
	 *            Properties to Load from, System.getProperties if null
	 * @param propertyName
	 *            Property Key
	 * @return Property Value, Null if not found
	 */
	private String getProperty(Properties properties, String propertyName) {
		String defaultPropertyValue = System.getProperty(propertyName);

		if (null == properties)
			return defaultPropertyValue;

		return properties.getProperty(propertyName, defaultPropertyValue);
	}

	/**
	 * Finishes Up the Current Connection
	 * 
	 * @see java.io.OutputStream#close()
	 */
	public void close() throws IOException {
		this.outputStream.close();

		this.jschChannel.disconnect();
		this.jschSession.disconnect();
	}

	/**
	 * Generic Equals Impl
	 * 
	 * @see java.lang.Object#equals(java.lang.Object)
	 */
	public boolean equals(Object obj) {
		return outputStream.equals(obj) || (this == obj);
	}

	/**
	 * Flushes Up the Underlying OutputStream
	 * 
	 * @see java.io.OutputStream#flush()
	 */
	public void flush() throws IOException {
		outputStream.flush();
	}

	/**
	 * Writes b[off:off+len-1] to remote endpoint
	 * 
	 * @param b
	 *            byte[] byte array to write
	 * @param off
	 *            offset to write
	 * @param len
	 *            length of the section to write
	 * @see java.io.OutputStream#write(byte[], int, int)
	 * @throws IOException
	 *             Network / I/O Failure
	 */
	public void write(byte[] b, int off, int len) throws IOException {
		outputStream.write(b, off, len);
	}

	/**
	 * Writes b to remote endpoint
	 * 
	 * @param b
	 *            byte[] byte array to write
	 * @see java.io.OutputStream#write(byte[])
	 * @throws IOException
	 *             Network / I/O Failure
	 */
	public void write(byte[] b) throws IOException {
		outputStream.write(b);
	}

	/**
	 * Writes b over to [this]
	 * 
	 * @param b
	 *            int character to write remotely (cast to a single byte value)
	 * @see java.io.OutputStream#write(int)
	 * @throws IOException
	 *             Network / I/O Failure
	 */
	public void write(int b) throws IOException {
		outputStream.write(b);
	}

	/**
	 * Getter for the Remote stdout as an InputStream
	 * 
	 * @see InputStream
	 * @return Remote stdout as an InputStream
	 */
	public PipedInputStream getRemoteOutputInputStream() {
		return remoteOutputInputStream;
	}

	/**
	 * Getter for the Remote stderr as an InputStream
	 * 
	 * @see InputStream
	 * @return Remote stdout as an InputStream
	 */
	public PipedInputStream getRemoteErrorInputStream() {
		return remoteErrorInputStream;
	}
}

package mm.eclipse.trac;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.Writer;

import mm.eclipse.trac.models.WikiPage;

import org.eclipse.core.runtime.IPath;

public class WikiPageCache
{

    public InputStream getPage( WikiPage wikiPage )
    {
        IPath path = Activator.getDefault().getStateLocation();
        path = path.append( "wiki-cache" );
        path = path.append( wikiPage.getServer().getName() );
        path.toFile().mkdirs();
        path = path.append( getFilename( wikiPage.getFullName() ) );

        File file = path.toFile();

        boolean downloadContent = false;
        if ( !file.exists() )
            downloadContent = true;
        else
        {
            BufferedReader reader;

            int version = 0;
            boolean dirty = false;

            try
            {
                reader = new BufferedReader( new FileReader( file ) );

                version = Integer.parseInt( reader.readLine().split( " " )[1] );
                dirty = reader.readLine().split( " " )[1].equals( "true" );
                reader.readLine();
            }
            catch ( IOException e )
            {
                Log.error( "Error reading file", e );
            }

            if ( wikiPage.getVersion() != version )
                // We have an outdated copy
                downloadContent = true;

            if ( dirty )
                wikiPage.setDirty( true );
        }

        if ( downloadContent )
        {
            Log.info( "Downloading content for " + wikiPage.getFullName() );

            // Download page content
            String content = wikiPage.getServer().getWiki().getPage(
                    wikiPage.getFullName() );

            try
            {
                FileWriter writer = new FileWriter( path.toFile() );
                writer.write( getHeader( wikiPage ) );
                writer.write( content );
                writer.close();
                Log.info( "File Written" );
            }
            catch ( IOException e )
            {
                Log.warning( "Cannot write local wiki file", e );
            }
        }

        InputStream is;
        try
        {
            is = new FileInputStream( file );

            // Advance to the end of the header
            for ( int i = 0; i < 3; i++ )
                while (is.read() != '\n')
                    ;

            return is;
        }
        catch ( IOException e )
        {
            Log.error( "Error reading file", e );
        }

        return null;
    }

    public void putPage( WikiPage page, String content )
    {
        IPath path = Activator.getDefault().getStateLocation();
        path = path.append( "wiki-cache" );
        path = path.append( page.getServer().getName() );
        path.toFile().mkdirs();
        path = path.append( getFilename( page.getFullName() ) );

        try
        {
            Writer writer = new FileWriter( path.toFile() );
            writer.write( getHeader( page ) );
            writer.write( content );
            writer.close();
        }
        catch ( IOException e )
        {
            Log.error( "Error writing in wiki cache", e );
        }
    }

    public void checkPage( WikiPage page )
    {
        BufferedReader reader;

        int version = 0;
        boolean dirty = false;
        
        File file = getFile( page );
        if ( ! file.exists() )
            return;

        try
        {
            reader = new BufferedReader( new FileReader( file ) );

            version = Integer.parseInt( reader.readLine().split( " " )[1] );
            dirty = reader.readLine().split( " " )[1].equals( "true" );
            
            reader.close();
        }
        catch ( IOException e )
        {
            Log.error( "Error reading file", e );
        }

        // if ( page.getVersion() != version )
            // We have an outdated copy
        //    ; 

        if ( dirty )
            page.setDirty( true );
    }

    private File getFile( WikiPage page )
    {
        IPath path = Activator.getDefault().getStateLocation();
        path = path.append( "wiki-cache" );
        path = path.append( page.getServer().getName() );
        path.toFile().mkdirs();
        path = path.append( getFilename( page.getFullName() ) );
        return path.toFile();
    }

    private String getHeader( WikiPage page )
    {
        StringBuilder sb = new StringBuilder();
        sb.append( "Version: " ).append( page.getVersion() ).append( '\n' );
        sb.append( "Dirty: " ).append( page.isDirty() ).append( '\n' );
        sb.append( "/////////////////////////////\n" );

        return sb.toString();
    }

    private String getFilename( String name )
    {
        name = name.replace( '/', '_' );
        return name;
    }
}

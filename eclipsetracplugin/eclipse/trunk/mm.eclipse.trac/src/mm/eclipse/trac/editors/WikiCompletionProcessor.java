/**
 * 
 */
package mm.eclipse.trac.editors;

import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;

import mm.eclipse.trac.Activator;
import mm.eclipse.trac.editors.model.WikiMacro;
import mm.eclipse.trac.xmlrpc.Trac;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.jface.resource.ImageRegistry;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextSelection;
import org.eclipse.jface.text.ITextViewer;
import org.eclipse.jface.text.Region;
import org.eclipse.jface.text.contentassist.CompletionProposal;
import org.eclipse.jface.text.contentassist.ContextInformation;
import org.eclipse.jface.text.contentassist.ICompletionProposal;
import org.eclipse.jface.text.contentassist.IContentAssistProcessor;
import org.eclipse.jface.text.contentassist.IContextInformation;
import org.eclipse.jface.text.contentassist.IContextInformationValidator;
import org.eclipse.jface.text.templates.DocumentTemplateContext;
import org.eclipse.jface.text.templates.Template;
import org.eclipse.jface.text.templates.TemplateContext;
import org.eclipse.jface.text.templates.TemplateContextType;
import org.eclipse.jface.text.templates.TemplateException;
import org.eclipse.jface.text.templates.TemplateProposal;
import org.eclipse.swt.graphics.Image;

public class WikiCompletionProcessor implements IContentAssistProcessor
{
    
    static class StringComparator implements Comparator
    {
        public int compare( Object o1, Object o2 )
        {
            String s1 = (String) o1;
            String s2 = (String) o2;
            return s1.compareTo( s2 );
        }
        
        public boolean equals( Object o )
        {
            return compare( this, o ) == 0;
        }
    }
    
    private static final String    TemplateIcon    = "icons/template.gif";
    
    private static final String    WordIcon        = "icons/word.png";
    
    private static final String    MacroIcon       = "icons/macro.gif";
    
    private static final String    TemplateContext = "mm.eclipse.trac.templates";
    
    private static List<WikiMacro> macros          = null;
    
    private final WikiSourceEditor editor;
    
    public WikiCompletionProcessor( WikiSourceEditor editor )
    {
        this.editor = editor;
    }
    
    public ICompletionProposal[] computeCompletionProposals( ITextViewer viewer,
                                                             int offset )
    {
        ITextSelection selection = (ITextSelection) viewer.getSelectionProvider()
                .getSelection();
        
        // adjust offset to start of normalized selection:
        if ( selection.getOffset() != offset )
        {
            offset = selection.getOffset();
        }
        
        String prefix = getPrefix( viewer, offset );
        Region region = new Region( offset - prefix.length(), prefix.length()
                                                              + selection.getLength() );
        
        List<ICompletionProposal> result = new ArrayList<ICompletionProposal>();
        
        List<ICompletionProposal> templateProposals = computeTemplateProposals( viewer,
                                                                                region,
                                                                                prefix );
        
        List<ICompletionProposal> wordProposals = computeWordProposals( viewer, region,
                                                                        prefix );
        
        List<ICompletionProposal> macroProposals = computeMacroProposals( viewer, region,
                                                                          prefix );
        result.addAll( wordProposals );
        result.addAll( macroProposals );
        result.addAll( templateProposals );
        
        return result.toArray( new ICompletionProposal[result.size()] );
    }
    
    private TemplateContextType getContextType()
    {
        return Activator.getDefault().getContextTypeRegistry()
                .getContextType( TemplateContext );
    }
    
    private TemplateContext createContext( ITextViewer viewer, IRegion region )
    {
        TemplateContextType contextType = getContextType();
        if ( contextType != null )
        {
            IDocument document = viewer.getDocument();
            return new DocumentTemplateContext( contextType, document,
                                                region.getOffset(), region.getLength() );
        }
        return null;
    }
    
    private List<ICompletionProposal> computeMacroProposals( ITextViewer viewer,
                                                             IRegion region, String prefix )
    {        
        List<ICompletionProposal> result = new ArrayList<ICompletionProposal>();
        
        for ( WikiMacro macro : getMacros() )
        {
            if ( macro.getName().toLowerCase().startsWith( prefix ) )
            {
                String replace = MessageFormat.format( "[[{0}()]]", macro.getName() );
                IContextInformation info = new ContextInformation( "Macro", macro
                        .getDescription() );
                ICompletionProposal prop = new CompletionProposal( replace, region
                        .getOffset(), prefix.length(), replace.length() - 3,
                                                                   getImage( MacroIcon ),
                                                                   macro.getName(), info,
                                                                   "Bla bla bla bla" );
                result.add( prop );
            }
        }
        
        return result;
    }
    
    private List<ICompletionProposal> computeWordProposals( ITextViewer viewer,
                                                            IRegion region, String prefix )
    {
        if ( prefix.length() == 0 ) return new ArrayList<ICompletionProposal>();
        
        Set<String> words = new HashSet<String>();
        
        String content = editor.getDocument().get();
        StringBuilder sb = new StringBuilder();
        
        for ( int i = 0; i < content.length(); i++ )
        {
            // We should ignore the current typed word
            if ( i == region.getOffset() ) continue;
            
            char c = content.charAt( i );
            
            if ( (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') )
            {
                sb.append( c );
            }
            else if ( sb.length() > 3 )
            {
                String word = sb.toString();
                if ( word.toLowerCase().startsWith( prefix ) )
                {
                    words.add( word );
                }
                sb = new StringBuilder();
            }
            else
            {
                sb = new StringBuilder();
            }
        }
        
        List<String> list = new ArrayList<String>( words );
        Collections.sort( list );
        
        List<ICompletionProposal> result = new ArrayList<ICompletionProposal>( list
                .size() );
        
        for ( String word : list )
        {
            // String message = MessageFormat.format( "test {0}", word );
            result.add( new CompletionProposal( word, region.getOffset(),
                                                prefix.length(), word.length(),
                                                getImage( WordIcon ), null, null, null ) );
        }
        
        return result;
    }
    
    private List<ICompletionProposal> computeTemplateProposals( ITextViewer viewer,
                                                                IRegion region,
                                                                String prefix )
    {
        TemplateContext context = createContext( viewer, region );
        if ( context == null ) { return new ArrayList<ICompletionProposal>(); }
        
        ITextSelection selection = (ITextSelection) viewer.getSelectionProvider()
                .getSelection();
        context.setVariable( "selection", selection.getText() );
        
        String id = context.getContextType().getId();
        Template[] templates = Activator.getDefault().getTemplateStore()
                .getTemplates( id );
        
        List<ICompletionProposal> matches = new ArrayList<ICompletionProposal>();
        
        for ( Template template : templates )
        {
            try
            {
                context.getContextType().validate( template.getPattern() );
                
            } catch ( TemplateException e )
            {
                continue;
            }
            
            if ( !template.getName().toLowerCase().startsWith( prefix ) ) continue;
            
            matches.add( new TemplateProposal( template, context, region,
                                               getImage( TemplateIcon ), 1 ) );
        }
        
        // Collections.sort( matches, proposalComparator );
        return matches;
    }
    
    private static List<WikiMacro> getMacros()
    {
        if ( macros != null ) return macros;
        
        Map<String, String> macroMap = Trac.getInstance().getWikiExt().getMacros();
        
        macros = new ArrayList<WikiMacro>( macroMap.size() );
        for ( Entry<String, String> entry : macroMap.entrySet() )
        {
            macros.add( new WikiMacro( entry.getKey(), entry.getValue() ) );
        }
        return macros;
    }
    
    private String getPrefix( ITextViewer viewer, int offset )
    {
        int i = offset;
        IDocument document = viewer.getDocument();
        if ( i > document.getLength() ) return "";
        
        try
        {
            while ( i > 0 )
            {
                char ch = document.getChar( i - 1 );
                if ( !Character.isLetterOrDigit( ch ) && (ch != ':') && (ch != '_') )
                    break;
                i--;
            }
            
            return document.get( i, offset - i ).toLowerCase();
        } catch ( BadLocationException e )
        {
            return "";
        }
    }
    
    /**
     * Always return the default image.
     */
    private Image getImage( String icon )
    {
        ImageRegistry registry = Activator.getDefault().getImageRegistry();
        Image image = registry.get( icon );
        if ( image == null )
        {
            ImageDescriptor desc = Activator.getImageDescriptor( icon );
            registry.put( icon, desc );
            image = registry.get( icon );
        }
        return image;
    }
    
    public IContextInformation[] computeContextInformation( ITextViewer viewer, int offset )
    {
        return null;
    }
    
    public char[] getCompletionProposalAutoActivationCharacters()
    {
        return null;
    }
    
    public char[] getContextInformationAutoActivationCharacters()
    {
        return null;
    }
    
    public String getErrorMessage()
    {
        return null;
    }
    
    public IContextInformationValidator getContextInformationValidator()
    {
        return null;
    }
}

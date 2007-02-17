package mm.eclipse.trac.models;

import java.util.Date;

public class WikiPageVersion
{
    private WikiPage page;
    
    private int      version;
    private String   author;
    private String   comment;
    private Date     date;
    
    public WikiPageVersion( WikiPage page, int version, String author, String comment,
                            Date date )
    {
        this.page = page;
        this.version = version;
        this.author = author;
        this.comment = comment;
        this.date = date;
    }
    
    public String toString()
    {
        return "Version " + version + " | " + author + " | " + comment + " | " + date;
    }
    
    public String getAuthor()
    {
        return author;
    }
    
    public String getComment()
    {
        return comment;
    }
    
    public Date getDate()
    {
        return date;
    }
    
    public WikiPage getPage()
    {
        return page;
    }
    
    public int getVersion()
    {
        return version;
    }
    
}

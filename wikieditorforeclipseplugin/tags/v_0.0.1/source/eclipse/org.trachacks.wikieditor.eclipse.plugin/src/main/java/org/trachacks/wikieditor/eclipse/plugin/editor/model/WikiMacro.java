package org.trachacks.wikieditor.eclipse.plugin.editor.model;

public class WikiMacro
{
    private String name;
    private String description;
    
    public WikiMacro( String name, String description )
    {
        this.name = name;
        this.description = description;
    }
    
    public String getDescription()
    {
        return description;
    }
    
    public String getName()
    {
        return name;
    }
    
}

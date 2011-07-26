/**
 * 
 */
package org.trachacks.wikieditor.model;

import java.util.Date;

/**
 * @author ivan
 *
 */
public class PageInfo extends AbstractBaseObject {

	private Long serverId;
	private String name;
    private Integer version = 0;
    private Date date;
    private String author;
    private String comment;
    
    
    public Long getServerId() {
		return serverId;
	}
	public String getName() {
		return name;
	}
	public Integer getVersion() {
		return version;
	}
	public Date getDate() {
		return date;
	}
	public String getAuthor() {
		return author;
	}
	public String getComment() {
		return comment;
	}
	
	public void setServerId(Long serverId) {
		this.serverId = serverId;
	}
	public void setName(String name) {
		this.name = name;
	}
	public void setVersion(Integer version) {
		this.version = version;
	}
	public void setDate(Date lastModified) {
		this.date = lastModified;
	}
	public void setAuthor(String author) {
		this.author = author;
	}
	public void setComment(String comment) {
		this.comment = comment;
	}
    
    
    
}

# -*- coding: utf8 -*-

def get_all(com, sql, *params):
    """Executes the query and returns the (description, data)"""
    db = com.env.get_db_cnx()
    cur = db.cursor()
    desc  = None
    data = None
    try:
        cur.execute(sql, params)
        data = list(cur.fetchall())
        desc = cur.description
        db.commit();
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, params, e));
        db.rollback();
    try:
        db.close()
    except:
        pass

    return (desc, data)

def get_first_row(com, sql, *params):
    """Executes the query and returns the (description, data)"""
    db = com.env.get_db_cnx()
    cur = db.cursor()
    desc  = None
    data = None
    try:
        cur.execute(sql, params)
        data = cur.fetchone()
        desc = cur.description
        db.commit();
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, params, e));
        db.rollback();
    try:
        db.close()
    except:
        pass

    return (desc, data)

def get_all_dict(com, sql, *params):
    """Executes the query and returns a Result Set"""
    desc, rows = get_all(com, sql, *params);
    if not desc:
        return []

    results = []
    for row in rows:
        row_dict = {}
        for field, col in zip(row, desc):
            row_dict[col[0]] = field
        results.append(row_dict)
    return results

def execute_sql(com, sql, *params):
    db = com.env.get_db_cnx()
    cur = db.cursor()

    try:
        cur.execute(sql, params)
        db.commit();
    except Exception, e:
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, params, e));
        db.rollback();
    try:
        db.close()
    except:
        pass
    

def findAvailableReleases(com):
    """Find all created releases, closed and open"""
    sql = "SELECT id, version, description, author, creation_date, planned_date, install_date FROM releases ORDER BY version DESC"
    return get_all_dict(com, sql)
    
def findAvailableVersions(com):
    """Find all registered versions"""
    sql = "SELECT name, time, description FROM version ORDER BY time DESC"
    return get_all_dict(com, sql)

def loadReleaseTickets(com, releaseId):
    sql = """SELECT rt.release_id,
                    rt.ticket_id,
                    t.type,
                    t.component,
                    t.version,
                    t.summary,
                    t.description
             FROM release_tickets rt,
                  ticket t
             WHERE rt.release_id = %s
               AND rt.ticket_id = t.id"""
               
    return get_all_dict(com, sql, releaseId)
    
    
def loadReleaseSignatures(com, releaseId):
    """Load all users who should sign this Release."""
    sql = """SELECT rs.signature,
                    rs.sign_date
             FROM release_signatures rs
             WHERE rs.release_id = %s"""
               
    return get_all_dict(com, sql, releaseId)


def loadRelease(com, releaseId):
    """Load data"""
    sql = "SELECT * FROM releases WHERE id = %s"
    desc, row = get_first_row(com, sql, releaseId);
    ret = {}
    for field, col in zip(row, desc):
        ret[col[0]] = field
    
    ret['tickets'] = loadReleaseTickets(com, releaseId)
    ret['signatures'] = loadReleaseSignatures(com, releaseId)
    return ret

def signRelease(com, releaseId, userName):
    """Marks a Release as signed by the indicated user"""
    sql = "UPDATE release_signatures SET sign_date = UNIX_TIMESTAMP() WHERE release_id = %s AND signature = %s"
    get_first_row(com, sql, releaseId, userName)
    
    
def getVersionTickets(com, version):
    """Load all tickets that are associated to the indicated version"""
    sql = """SELECT t.id, t.summary, t.component, t.type, t.version FROM ticket t WHERE t.version = %s"""
    return get_all_dict(com, sql, version)
    
    
def getTicket(com, ticketId):
    """Load some data from the indicated ticket"""
    sql = """SELECT t.id, t.summary, t.component, t.type, t.version FROM ticket t WHERE t.id = %s"""
    ret = get_all_dict(com, sql, ticketId)
    if ret:
        return ret[0]
    return []
    
    
def createRelease(com, name, description, author, planned, tickets, signatures):
    sql = """INSERT INTO releases (version, description, author, creation_date, planned_date) VALUES (%s, %s, %s, NOW(), %s)"""
    sqlTickets = """INSERT INTO release_tickets (release_id, ticket_id) VALUES (%s, %s)"""
    sqlSignatures = """INSERT INTO release_signatures (release_id, signature) VALUES (%s, %s)"""

    db = com.env.get_db_cnx()
    cur = db.cursor()
    
    flag = True
    
    try:
        cur.execute(sql, (name, description, author, planned))
    except Exception, e:
        flag = False
        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sql, (name, description, author, planned), e));
        db.rollback()
        
    if flag:
        relId = db.get_last_id(cur, 'releases')
        if relId:
            for ticket in tickets.split(","):
                ticket = ticket.strip()
                try:
                    ticket = int(ticket)
                except:
                    ticket = 0
                    
                if ticket:
                    try:                
                        cur.execute(sqlTickets, (relId, ticket))
                    except Exception, e:
                        flag = False
                        com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sqlTickets, (relId, ticket), e));
                        db.rollback()
                        break
                    
            if flag:
                for sign in signatures.split(","):
                    sign = sign.strip()
                    if sign:
                        try:    
                            cur.execute(sqlSignatures, (relId, sign))
                        except Exception, e:
                            flag = False
                            com.log.error('There was a problem executing sql:%s \n with parameters:%s\nException:%s'%(sqlSignatures, (relId, sign), e));
                            db.rollback()
                            break
        
        if flag:
            db.commit();
    try:
        db.close()
    except:
        pass

    
    
    
    
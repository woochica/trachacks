import dbhelper

estimateUpdate = """
UPDATE estimate SET rate=%s, variability=%s, communication=%s, tickets=%s, comment=%s,
   diffcomment=%s, saveepoch=%s, summary=%s
WHERE id=%s
"""
estimateInsert = """
INSERT INTO estimate (rate, variability, communication, tickets, comment, diffcomment, saveepoch, summary, id)
VALUES(%s,%s,%s,%s,%s,%s,%s,%s, %s)
"""
lineItemInsert = """
INSERT INTO estimate_line_item (estimate_id, description, low, high, ordinal, id)
VALUES (%s,%s,%s,%s,%s,%s)
"""
lineItemUpdate = """
UPDATE estimate_line_item SET estimate_id=%s ,
  description=%s, low=%s, high=%s, ordinal=%s
WHERE id=%s
"""
estimateIdSql = "SELECT MAX(id) FROM estimate"
estimateLineItemIdSql = "SELECT MAX(id) FROM estimate_line_item"

def nextEstimateId (env):
    return (dbhelper.get_scalar(env, estimateIdSql) or 0)+1

def nextEstimateLineItemId (env):
    return (dbhelper.get_scalar(env, estimateLineItemIdSql) or 0)+1

def getEstimateResultSet(env, id):
    return dbhelper.get_result_set(env, "SELECT * FROM estimate WHERE id=%s", id)

def getEstimateLineItemsResultSet(env, id):
    return dbhelper.get_result_set(env, "SELECT * FROM estimate_line_item WHERE estimate_id=%s", id)

removeLineItemsNotInListSql = """
DELETE FROM estimate_line_item
WHERE estimate_id=%%s and id not in (%s)
"""

    
def getHtmlEstimate(env, id):
    return dbhelper.get_scalar(env, "SELECT COMMENT FROM estimate WHERE ID=%s", 0, id)

def getTextEstimate(env, id):
    return dbhelper.get_scalar(env, "SELECT DIFFCOMMENT FROM estimate WHERE ID=%s", 0, id)

estimateChangeTicketComment = """
INSERT INTO ticket_change (ticket, time, author, field, oldvalue, newvalue)
VALUES ( %s, %s, %s, 'comment', %s, %s )
"""

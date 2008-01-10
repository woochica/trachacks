import dbhelper

estimateUpdate = """
UPDATE estimate SET rate=%s, variability=%s, communication=%s, tickets=%s
WHERE id=%s
"""
estimateInsert = """
INSERT INTO estimate (rate, variability, communication, tickets, id)
VALUES(%s,%s,%s,%s,%s)
"""
lineItemInsert = """
INSERT INTO estimate_line_item (estimate_id, description, low, high, id)
VALUES (%s,%s,%s,%s,%s)
"""
lineItemUpdate = """
UPDATE estimate_line_item SET estimate_id=%s ,
  description=%s, low=%s, high=%s
WHERE id=%s
"""
estimateIdSql = "SELECT MAX(id) FROM estimate"
estimateLineItemIdSql = "SELECT MAX(id) FROM estimate_line_item"

def nextEstimateId ():
    return (dbhelper.get_scalar(estimateIdSql) or 0)+1

def nextEstimateLineItemId ():
    return (dbhelper.get_scalar(estimateLineItemIdSql) or 0)+1

def getEstimateResultSet(id):
    return dbhelper.get_result_set("SELECT * FROM estimate WHERE id=%s", id)

def getEstimateLineItemsResultSet(id):
    return dbhelper.get_result_set("SELECT * FROM estimate_line_item WHERE estimate_id=%s", id)

removeLineItemsNotInListSql = """
DELETE FROM estimate_line_item
WHERE estimate_id=%%s and id not in (%s)
"""

    

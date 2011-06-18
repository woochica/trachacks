import sqlite3
import shutil
import os
from trac.core import *
from trac.mimeview.api import Mimeview


class ZoteroModelProvider(Component):
    db = []
    ref_fields = ['date', 'volume', 'issue', 'publicationTitle', 'pages', 'url']
    all_fields_id = {}
    all_fields_name = {}
    item_infor_field = ['itemTypeID', 'dateAdded', 'dateModified', 'clientDateModified', 'libraryID', 'key' ]
    
    def __init__(self):
        db_path = self.env.config.get('zotero', 'path' )
        dbname = self.env.config.get('zotero', 'dbname', 'zotero.sqlite' )
        if not db_path:
            raise Exception( 'path must be specified')
        if not dbname:
            raise Exception( 'dbname must be specified')
        full_path = self.env.path + '\\htdocs\\' + db_path + '\\' + dbname
        temp_path = full_path+'.trac'
        if not os.path.exists(temp_path):
            shutil.copyfile( full_path, temp_path)
        #raise Exception(full_path.replace('\\','/'))
        self.db = sqlite3.connect(str(temp_path), check_same_thread = False)
        sql = 'SELECT fieldID, fieldName FROM fieldsCombined'
        c = self.db.cursor()
        c.execute( sql )
        fields= {}
        for id, name in c:
            self.all_fields_id[id] = name
            self.all_fields_name[name] = id
    def restart(self):
        c = self.db.cursor()
        c.close()
        db_path = self.env.config.get('zotero', 'path' )
        dbname = self.env.config.get('zotero', 'dbname', 'zotero.sqlite' )
        if not db_path:
            raise Exception( 'path must be specified')
        if not dbname:
            raise Exception( 'dbname must be specified')
        full_path = self.env.path + '\\htdocs\\' + db_path + '\\' + dbname
        temp_path = full_path+'.trac'
        shutil.copyfile( full_path, temp_path)
        self.db = sqlite3.connect(str(temp_path), check_same_thread = False)
        sql = 'SELECT fieldID, fieldName FROM fieldsCombined'
        c = self.db.cursor()
        c.execute( sql )
        fields= {}
        for id, name in c:
            self.all_fields_id[id] = name
            self.all_fields_name[name] = id
        
    def item_exist(self, item_id):
        sql = 'SELECT COUNT(*) FROM items WHERE itemID='+str(item_id)
        c = self.db.cursor()
        c.execute( sql )
        for row in c:
            if row:
                return 1
        return 0
    def get_item_collections(self, item_id):
        sql = "SELECT collectionID FROM collectionItems "  
        sql += "WHERE itemID=" 
        sql += str(item_id)
        c = self.db.cursor()
        c.execute( sql )
        col = []
        for row in c:
            col.append(row)
        return col
    def get_all_item(self, onlyTopLevel, libraryID, includeDeleted):
        sql = 'SELECT A.itemID FROM items A'
        if ( onlyTopLevel ):
            sql += ' LEFT JOIN itemNotes B USING (itemID) '
            sql += 'LEFT JOIN itemAttachments C ON (C.itemID=A.itemID) '
            sql += 'WHERE B.sourceItemID IS NULL AND C.sourceItemID IS NULL'
        else:
            sql += " WHERE 1"
        if (not includeDeleted):    
            sql += " AND A.itemID NOT IN (SELECT itemID FROM deletedItems)"
        if (libraryID):
            sql += " AND libraryID=" + libraryID
        else:
            sql += " AND libraryID IS NULL"
        c = self.db.cursor()
        c.execute( sql )
        items = []
        for row in c:
            items.append(row[0])
        return items
    def get_items_id(self,keys):
        if keys:
            sql = 'SELECT itemID FROM items ' \
                + 'WHERE key in (' \
                + ', '.join(['\'' + str(x) + '\'' for x in keys]) \
                + ')'
            c = self.db.cursor()
            c.execute( sql )
            item_ids = []
            for item in c:
                item_ids.append(item[0])
            return item_ids
        return []
    def get_item_cites(self, itemids):
        sql = 'SELECT itemID,  ' + self.get_first_creator_sql() \
            + ', ( SELECT substr(value,1,4) FROM itemData ID NATURAL JOIN itemDataValues WHERE ID.fieldID == 14 AND I.itemID = ID.itemID ) AS year ' \
            + ' FROM items I WHERE itemID  in ('  \
            +', '.join([str(x) for x in itemids]) \
            + ')'
        c = self.db.cursor()
        c.execute( sql )
        return [i for i in c]
    def get_item_fields(self, itemids, fields,order=[], desc=[]):
        sql = 'SELECT itemID'
        for field in fields:
            if field in self.item_infor_field:
                sql += ', ' +  field
            elif field == 'numNotes':
                sql += ", (SELECT COUNT(*) FROM itemNotes INo WHERE sourceItemID=I.itemID AND "
                sql += "INo.itemID NOT IN (SELECT itemID FROM deletedItems)) AS numNotes"
            elif field == 'numAttachments':
                sql += ", (SELECT COUNT(*) FROM itemAttachments IA WHERE sourceItemID=I.itemID AND "
                sql += "IA.itemID NOT IN (SELECT itemID FROM deletedItems)) AS numAttachments "
            elif 'firstCreator' == field:
                sql += ', ' + self.get_first_creator_sql()
            elif 'year' == field:
                sql += ', ( SELECT substr(value,1,4) FROM itemData ID NATURAL JOIN itemDataValues WHERE ID.fieldID == 14 AND I.itemID = ID.itemID ) AS year '
            elif 'itemType' == field:
                sql += ', ( SELECT ITC.typeName FROM itemTypesCombined ITC WHERE I.itemTypeID == ITC.itemTypeID ) AS typeName '
            elif self.all_fields_name.has_key(field):
                    sql += ', ( SELECT value FROM itemData ID NATURAL JOIN itemDataValues WHERE ID.fieldID == ' 
                    sql += str( self.all_fields_name[field] ) + ' AND I.itemID = ID.itemID ) AS ' + field
        sql += ' FROM items I WHERE itemID  in ('
        sql += ', '.join([str(x) for x in itemids]) 
        sql += ')'
        #self.log.debug(sql)
        if order:
            sql += ' ORDER BY ' + order
        if desc:
            sql += ' DESC'
        c = self.db.cursor()
        c.execute( sql )
        to_unicode = Mimeview(self.env).to_unicode
        return [[to_unicode(j) for j in i] for i in c]
    def get_item_field_value(self,itemid):
        if not itemid:
            return []
        sql = 'SELECT itemID, fieldID, value'
        sql += ', (SELECT itemTypeID FROM items I NATURAL JOIN itemTypesCombined ITC WHERE ID.itemID = I.itemID) AS itemTypeID' 
        sql += ', (SELECT orderIndex FROM itemTypeFieldsCombined ITFC WHERE ITFC.fieldID = ID.fieldID) AS orderIndex'
        sql += ', (SELECT fieldName FROM fieldsCombined FC WHERE FC.fieldID = ID.fieldID) AS fieldName'
        sql += ' FROM itemData ID NATURAL JOIN itemDataValues WHERE itemID = ' + str( itemid )
        sql += ' ORDER BY orderIndex'
        c = self.db.cursor()
        c.execute( sql )
        to_unicode = Mimeview(self.env).to_unicode
        return [[to_unicode(j) for j in i] for i in c]
    def get_item_refs(self, itemids):
        sql = 'SELECT itemID,  ' + self.get_first_creator_sql() + ','\
            + '( SELECT value FROM itemData ID NATURAL JOIN itemDataValues WHERE ID.fieldID = 14 ) AS year ' \
            + ' FROM items I WHERE itemID  in ('  \
            +', '.join([str(x) for x in itemids]) \
            + ')'
        c = self.db.cursor()
        c.execute( sql )
        return [[id,fc,y[(len(y)-4):]] for id,fc,y in c]
    def get_attachment(self, itemids):
        if not itemids:
            return []
        sql = 'SELECT sourceItemID, itemID, mimeType, path'
        sql += ', (SELECT key FROM items I WHERE IA.itemID = I.itemID) AS key'
        sql += ' FROM itemAttachments IA WHERE sourceItemID in ('
        sql += ', '.join([str(x) for x in itemids]) 
        sql += ')'
        sql += ' AND IA.itemID NOT IN (SELECT itemID FROM deletedItems)'
        c = self.db.cursor()
        c.execute( sql )
        to_unicode = Mimeview(self.env).to_unicode
        return [[to_unicode(j) for j in i] for i in c]
    def get_related(self,itemids):
        if not itemids:
            return []
        sql = 'SELECT * FROM itemSeeAlso WHERE itemID in ('
        sql += ', '.join([str(x) for x in itemids]) 
        sql += ')'
        sql += ' OR linkedItemID in ( '
        sql += ', '.join([str(x) for x in itemids]) 
        sql += ')'
        c = self.db.cursor()
        c.execute( sql )
        return [i for i in c]
    def get_creators(self,item_id):
        if item_id:
            sql = 'SELECT IC.itemID, IC.creatorID, CD.firstName, CD.lastName FROM itemCreators IC NATURAL JOIN creators' \
                + ' NATURAL JOIN creatorData CD WHERE itemID=' \
                + str(item_id) \
                + ' ORDER BY orderIndex'
            c = self.db.cursor()
            c.execute( sql )
            return [item for item in c] 
        return []
    def get_first_creator(self,item_ids):
        if item_ids:
            sql = 'SELECT itemID, ' + self.get_first_creator_sql() \
                + ' FROM items I WHERE itemID  in ('  \
                +', '.join([str(x) for x in item_ids]) \
                + ')'
            c = self.db.cursor()
            c.execute( sql )
            return [item for item in c] 
        return []
    def get_root_collections(self):
        sql = 'SELECT C.collectionID, C.collectionName, C.parentCollectionID,  '
        sql += '(SELECT COUNT(*) FROM collections WHERE '
        sql += 'parentCollectionID=C.collectionID)!=0 AS hasChildCollections, '
        sql += '(SELECT COUNT(*) FROM collectionItems WHERE '
        sql += 'collectionID=C.collectionID)!=0 AS hasChildItems '
        sql += 'FROM collections C '
        sql += 'WHERE parentCollectionID IS NULL ORDER BY collectionName'

        c = self.db.cursor()
        c.execute( sql )
        root_collection = []
        for row in c:
            root_collection.append(row)
        return root_collection
    def get_child_collections(self,col_id):
        sql = 'SELECT C.collectionID, C.collectionName, C.parentCollectionID,  '
        sql += '(SELECT COUNT(*) FROM collections WHERE '
        sql += 'parentCollectionID=C.collectionID)!=0 AS hasChildCollections, '
        sql += '(SELECT COUNT(*) FROM collectionItems WHERE '
        sql += 'collectionID=C.collectionID)!=0 AS hasChildItems '
        sql += 'FROM collections C '
        sql += 'WHERE parentCollectionID == ' + str( col_id )
        sql += ' ORDER BY collectionName'

        c = self.db.cursor()
        c.execute( sql )
        child_collection = []
        for row in c:
            child_collection.append(row)
        return child_collection
    def get_child_item(self, col_id):
        sql = 'SELECT itemID FROM collectionItems WHERE collectionID=' + str(col_id) + ' '
        sql += 'AND itemID NOT IN '
        sql += '(SELECT itemID FROM itemNotes WHERE sourceItemID IS NOT NULL) '
        sql += 'AND itemID NOT IN '
        sql += '(SELECT itemID FROM itemAttachments WHERE sourceItemID IS NOT NULL)'
        c = self.db.cursor()
        c.execute( sql )
        child_items = []
        for row in c:
            child_items.append(row[0])
        return child_items
    def search_by_creator(self, creatorid):
        if not creatorid:
            return []
        sql = 'SELECT itemID'
        sql += ' FROM itemCreators IC WHERE creatorID in ('
        sql += ', '.join([str(x) for x in creatorid]) 
        sql += ')'
        c = self.db.cursor()
        c.execute( sql )
        return [iid[0] for iid in c]
    def count_by_author(self):
        sql = 'SELECT creatorID, cnum, firstName, lastName FROM  ' \
            + '( SELECT creatorID, cnum, creatorDataID FROM' \
            + '( SELECT * FROM (SELECT creatorID, count(itemID) AS cnum' \
            + ' FROM itemCreators IC WHERE 1 GROUP BY creatorID) WHERE 1 )' \
            + ' NATURAL JOIN creators C ) ' \
            + 'NATURAL JOIN creatorData CD WHERE 1 ORDER BY lastName'
        c = self.db.cursor()
        c.execute( sql )
        return [iid for iid in c]
    def count_by_author_top(self, num=5):
        sql = 'SELECT C.creatorID, CD.firstName, CD.lastName ' \
            + 'FROM creators C NATURAL JOIN creatorData CD ' \
            + 'WHERE C.creatorID IN (SELECT creatorID FROM (' \
            + 'SELECT creatorID, count(itemID) AS cnum FROM itemCreators IC ' \
            + 'WHERE 1 GROUP BY creatorID ORDER BY cnum DESC) ' \
            + 'WHERE 1 LIMIT '+ str(5) +')' 
        c = self.db.cursor()
        c.execute( sql )
        to_unicode = Mimeview(self.env).to_unicode
        return [[to_unicode(j) for j in i] for i in c]
    def search_by_year(self, years):
        if not years:
            return []
        sql = 'SELECT itemID FROM'
        sql += ' ( SELECT itemID, substr(value,1,4) AS year FROM itemData ID NATURAL'
        sql += ' JOIN itemDataValues WHERE ID.fieldID == 14 ) WHERE year in ('
        sql += ', '.join(['\''+str(x)+'\'' for x in years]) 
        sql += ')'

        c = self.db.cursor()
        c.execute( sql )
        return [iid[0] for iid in c]
    def count_by_year(self):
        sql = 'SELECT year, COUNT(year) AS ynum  FROM ( SELECT itemID, substr(value,1,4) AS year FROM ' \
            + 'itemData ID NATURAL JOIN itemDataValues WHERE ID.fieldID == 14 ) ' \
            + 'WHERE 1 GROUP BY year ORDER BY year'
        c = self.db.cursor()
        c.execute( sql )
        return [iid for iid in c]
    def count_by_year_top(self, num=5):
        sql = 'SELECT year FROM ( SELECT year, COUNT(year) AS ynum  FROM ' \
            + '( SELECT itemID, substr(value,1,4)' \
            + 'AS year FROM itemData ID NATURAL JOIN ' \
            + 'itemDataValues WHERE ID.fieldID == 14 ) ' \
            + 'WHERE 1 GROUP BY year ORDER BY ynum desc ) LIMIT ' + str(num)
        c = self.db.cursor()
        c.execute( sql )
        return [y[0] for y in c]
    def search_by_publisher(self, publicationTitle):
        if not publicationTitle:
            return []
        ptid = self.all_fields_name['publicationTitle']
        sql = 'SELECT itemID FROM'
        sql += ' ( SELECT itemID, value AS year FROM itemData ID NATURAL'
        sql += ' JOIN itemDataValues WHERE ID.fieldID == ' + str(ptid) + ' ) WHERE year in ('
        sql += ', '.join(['\''+str(x)+'\'' for x in publicationTitle]) 
        sql += ')'
        c = self.db.cursor()
        c.execute( sql )
        return [iid[0] for iid in c]
    def count_by_publisher(self):
        ptid = self.all_fields_name['publicationTitle']
        sql = 'SELECT publisher, COUNT(publisher) AS pnum  FROM ( SELECT itemID, value AS publisher FROM ' \
            + 'itemData ID NATURAL JOIN itemDataValues WHERE ID.fieldID == '+str(ptid)+' ) ' \
            + 'WHERE 1 GROUP BY publisher ORDER BY publisher'
        c = self.db.cursor()
        c.execute( sql )
        return [iid for iid in c]
    def count_by_publisher_top(self, num=5):
        ptid = self.all_fields_name['publicationTitle']
        sql = 'SELECT publisher FROM ( SELECT publisher, COUNT(publisher) AS ynum  FROM ' \
            + '( SELECT itemID, value ' \
            + 'AS publisher FROM itemData ID NATURAL JOIN ' \
            + 'itemDataValues WHERE ID.fieldID == ' +str(ptid) + ') ' \
            + 'WHERE 1 GROUP BY publisher ORDER BY ynum desc ) LIMIT ' + str(num)
        c = self.db.cursor()
        c.execute( sql )
        return [y[0] for y in c]
    def get_recents(self, num=10):
        sql = 'SELECT A.itemID FROM items A'
        sql += ' LEFT JOIN itemNotes B USING (itemID)'
        sql += ' LEFT JOIN itemAttachments C ON (C.itemID=A.itemID)'
        sql += ' WHERE B.sourceItemID IS NULL AND C.sourceItemID IS NULL'  
        sql += ' AND A.itemID NOT IN (SELECT itemID FROM deletedItems)' 
        sql += ' ORDER BY dateModified DESC LIMIT '
        sql += str(num)
        c = self.db.cursor()
        c.execute( sql )
        return [y[0] for y in c]
    def get_first_creator_sql(self):
        localizedAnd = ' & '
        sql = "COALESCE(" + \
            "CASE (" + \
                "SELECT COUNT(*) FROM itemCreators IC " + \
                "LEFT JOIN itemTypeCreatorTypes ITCT " + \
                "ON (IC.creatorTypeID=ITCT.creatorTypeID AND ITCT.itemTypeID=I.itemTypeID) " + \
                "WHERE itemID=I.itemID AND primaryField=1" + \
            ") " + \
            "WHEN 0 THEN NULL " + \
            "WHEN 1 THEN (" + \
                "SELECT lastName FROM itemCreators IC NATURAL JOIN creators " + \
                "NATURAL JOIN creatorData " + \
                "LEFT JOIN itemTypeCreatorTypes ITCT " + \
                "ON (IC.creatorTypeID=ITCT.creatorTypeID AND ITCT.itemTypeID=I.itemTypeID) " + \
                "WHERE itemID=I.itemID AND primaryField=1" + \
            ") " + \
            "WHEN 2 THEN (" + \
                "SELECT " + \
                "(SELECT lastName FROM itemCreators IC NATURAL JOIN creators " + \
                "NATURAL JOIN creatorData " + \
                "LEFT JOIN itemTypeCreatorTypes ITCT " + \
                "ON (IC.creatorTypeID=ITCT.creatorTypeID AND ITCT.itemTypeID=I.itemTypeID) " + \
                "WHERE itemID=I.itemID AND primaryField=1 ORDER BY orderIndex LIMIT 1)" + \
                " || ' " + localizedAnd + " ' || " + \
                "(SELECT lastName FROM itemCreators IC NATURAL JOIN creators " + \
                "NATURAL JOIN creatorData " + \
                "LEFT JOIN itemTypeCreatorTypes ITCT " + \
                "ON (IC.creatorTypeID=ITCT.creatorTypeID AND ITCT.itemTypeID=I.itemTypeID) " + \
                "WHERE itemID=I.itemID AND primaryField=1 ORDER BY orderIndex LIMIT 1,1)" + \
            ") " + \
            "ELSE (" + \
                "SELECT " + \
                "(SELECT lastName FROM itemCreators IC NATURAL JOIN creators " + \
                "NATURAL JOIN creatorData " + \
                "LEFT JOIN itemTypeCreatorTypes ITCT " + \
                "ON (IC.creatorTypeID=ITCT.creatorTypeID AND ITCT.itemTypeID=I.itemTypeID) " + \
                "WHERE itemID=I.itemID AND primaryField=1 ORDER BY orderIndex LIMIT 1)" + \
                " || ' et al.' " + \
            ") " + \
            "END, " + \
            "CASE (" + \
                "SELECT COUNT(*) FROM itemCreators WHERE itemID=I.itemID AND creatorTypeID IN (3)" + \
            ") " + \
            "WHEN 0 THEN NULL " + \
            "WHEN 1 THEN (" + \
                "SELECT lastName FROM itemCreators NATURAL JOIN creators " + \
                "NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (3)" + \
            ") " + \
            "WHEN 2 THEN (" + \
                "SELECT " + \
                "(SELECT lastName FROM itemCreators NATURAL JOIN creators NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (3) ORDER BY orderIndex LIMIT 1)" + \
                " || ' " + localizedAnd + " ' || " + \
                "(SELECT lastName FROM itemCreators NATURAL JOIN creators NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (3) ORDER BY orderIndex LIMIT 1,1) " + \
            ") " + \
            "ELSE (" + \
                "SELECT " + \
                "(SELECT lastName FROM itemCreators NATURAL JOIN creators NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (3) ORDER BY orderIndex LIMIT 1)" + \
                " || ' et al.' " + \
            ") " + \
            "END, " + \
            "CASE (" + \
                "SELECT COUNT(*) FROM itemCreators WHERE itemID=I.itemID AND creatorTypeID IN (2)" + \
            ") " + \
            "WHEN 0 THEN NULL " + \
            "WHEN 1 THEN (" + \
                "SELECT lastName FROM itemCreators NATURAL JOIN creators " + \
                "NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (2)" + \
            ") " + \
            "WHEN 2 THEN (" + \
                "SELECT " + \
                "(SELECT lastName FROM itemCreators NATURAL JOIN creators NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (2) ORDER BY orderIndex LIMIT 1)" + \
                " || ' " + localizedAnd + " ' || " + \
                "(SELECT lastName FROM itemCreators NATURAL JOIN creators NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (2) ORDER BY orderIndex LIMIT 1,1) " + \
            ") " + \
            "ELSE (" + \
                "SELECT " + \
                "(SELECT lastName FROM itemCreators NATURAL JOIN creators NATURAL JOIN creatorData " + \
                "WHERE itemID=I.itemID AND creatorTypeID IN (2) ORDER BY orderIndex LIMIT 1)" + \
                " || ' et al.' " + \
            ") " + \
            "END" + \
        ") AS firstCreator"
        return sql
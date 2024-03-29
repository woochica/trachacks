
ref_fields = ['date', 'volume', 'issue', 'publicationTitle', 'pages', 'url']
creator_fields = ['firstName', 'lastName']
item_infor_fields = ['itemTypeID', 'dateAdded', 'dateModified', 'clientDateModified', 'libraryID', 'key' ]


# {'type': 'text', 'name': 'firstName', 'label': 'First Name'},
# {'type': 'text', 'name': 'lastName', 'label': 'Last Name'},
# mapping for zotero field
zotero_fields_mapping = [
    {'type': 'text', 'name': 'firstCreator', 'label': 'Authors'},
    {'type': 'text', 'name': 'publicationTitle', 'label': 'Publisher'},
    {'type': 'text', 'name': 'firstName', 'label': 'First Name'},
    {'type': 'text', 'name': 'lastName', 'label': 'Last Name'},
    {'type': 'text', 'name': 'year', 'label': 'Year'}, 
    {'type': 'text', 'name': 'date', 'label': 'Date'}, 
    {'type': 'text', 'name': 'title', 'label': 'Title'}, 
    {'type': 'text', 'name': 'url', 'label': 'URL'}, 
    {'type': 'text', 'name': 'rights', 'label': 'Rights'}, 
    {'type': 'text', 'name': 'series', 'label': 'Series'},
    {'type': 'text', 'name': 'volume', 'label': 'volume'},
    {'type': 'text', 'name': 'issue', 'label': 'issue'},
    {'type': 'text', 'name': 'edition', 'label': 'edition'}, 
    {'type': 'text', 'name': 'place', 'label': 'place'}, 
    {'type': 'text', 'name': 'publisher', 'label': 'publisher'}, 
    {'type': 'text', 'name': 'pages', 'label': 'pages'}, 
    {'type': 'text', 'name': 'ISBN', 'label': 'ISBN'}, 
    {'type': 'text', 'name': 'ISSN', 'label': 'ISSN'}, 
    {'type': 'text', 'name': 'section', 'label': 'section'}, 
    {'type': 'text', 'name': 'callNumber', 'label': 'Call No.'}, 
    {'type': 'text', 'name': 'archiveLocation', 'label': 'archiveLocation'}, 
    {'type': 'text', 'name': 'distributor', 'label': 'distributor'}, 
    {'type': 'text', 'name': 'extra', 'label': 'extra'}, 
    {'type': 'text', 'name': 'journalAbbreviation', 'label': 'Journal Abbr'}, 
    {'type': 'text', 'name': 'DOI', 'label': 'DOI'}, 
    {'type': 'text', 'name': 'accessDate', 'label': 'Access'}, 
    {'type': 'text', 'name': 'seriesTitle', 'label': 'seriesTitle'}, 
    {'type': 'text', 'name': 'seriesText', 'label': 'seriesText'}, 
    {'type': 'text', 'name': 'seriesNumber', 'label': 'seriesNumber'}, 
    {'type': 'text', 'name': 'institution', 'label': 'institution'}, 
    {'type': 'text', 'name': 'reportType', 'label': 'reportType'}, 
    {'type': 'text', 'name': 'code', 'label': 'code'}, 
    {'type': 'text', 'name': 'session', 'label': 'session'}, 
    {'type': 'text', 'name': 'legislativeBody', 'label': 'legislativeBody'}, 
    {'type': 'text', 'name': 'history', 'label': 'history'}, 
    {'type': 'text', 'name': 'reporter', 'label': 'reporter'}, 
    {'type': 'text', 'name': 'court', 'label': 'court'}, 
    {'type': 'text', 'name': 'numberOfVolumes', 'label': 'numberOfVolumes'}, 
    {'type': 'text', 'name': 'committee', 'label': 'committee'}, 
    {'type': 'text', 'name': 'assignee', 'label': 'assignee'}, 
    {'type': 'text', 'name': 'patentNumber', 'label': 'patentNumber'}, 
    {'type': 'text', 'name': 'priorityNumbers', 'label': 'priorityNumbers'}, 
    {'type': 'text', 'name': 'issueDate', 'label': 'issueDate'}, 
    {'type': 'text', 'name': 'references', 'label': 'references'}, 
    {'type': 'text', 'name': 'legalStatus', 'label': 'legalStatus'}, 
    {'type': 'text', 'name': 'codeNumber', 'label': 'codeNumber'}, 
    {'type': 'text', 'name': 'artworkMedium', 'label': 'artworkMedium'}, 
    {'type': 'text', 'name': 'number', 'label': 'number'}, 
    {'type': 'text', 'name': 'artworkSize', 'label': 'artworkSize'}, 
    {'type': 'text', 'name': 'libraryCatalog', 'label': 'Lib Cat'}, 
    {'type': 'text', 'name': 'videoRecordingFormat', 'label': 'videoRecordingFormat'}, 
    {'type': 'text', 'name': 'interviewMedium', 'label': 'interviewMedium'}, 
    {'type': 'text', 'name': 'letterType', 'label': 'letterType'}, 
    {'type': 'text', 'name': 'manuscriptType', 'label': 'manuscriptType'}, 
    {'type': 'text', 'name': 'mapType', 'label': 'mapType'}, 
    {'type': 'text', 'name': 'scale', 'label': 'scale'}, 
    {'type': 'text', 'name': 'thesisType', 'label': 'thesisType'}, 
    {'type': 'text', 'name': 'websiteType', 'label': 'websiteType'}, 
    {'type': 'text', 'name': 'audioRecordingFormat', 'label': 'audioRecordingFormat'}, 
    {'type': 'text', 'name': 'label', 'label': 'label'}, 
    {'type': 'text', 'name': 'presentationType', 'label': 'presentationType'}, 
    {'type': 'text', 'name': 'meetingName', 'label': 'meetingName'}, 
    {'type': 'text', 'name': 'studio', 'label': 'studio'}, 
    {'type': 'text', 'name': 'runningTime', 'label': 'runningTime'}, 
    {'type': 'text', 'name': 'network', 'label': 'network'}, 
    {'type': 'text', 'name': 'postType', 'label': 'postType'}, 
    {'type': 'text', 'name': 'audioFileType', 'label': 'audioFileType'}, 
    {'type': 'text', 'name': 'version', 'label': 'version'}, 
    {'type': 'text', 'name': 'system', 'label': 'system'}, 
    {'type': 'text', 'name': 'company', 'label': 'company'}, 
    {'type': 'text', 'name': 'conferenceName', 'label': 'conferenceName'}, 
    {'type': 'text', 'name': 'encyclopediaTitle', 'label': 'encyclopediaTitle'}, 
    {'type': 'text', 'name': 'dictionaryTitle', 'label': 'dictionaryTitle'}, 
    {'type': 'text', 'name': 'language', 'label': 'language'}, 
    {'type': 'text', 'name': 'programmingLanguage', 'label': 'programmingLanguage'}, 
    {'type': 'text', 'name': 'university', 'label': 'university'}, 
    {'type': 'text', 'name': 'abstractNote', 'label': 'abstractNote'}, 
    {'type': 'text', 'name': 'websiteTitle', 'label': 'websiteTitle'}, 
    {'type': 'text', 'name': 'reportNumber', 'label': 'reportNumber'}, 
    {'type': 'text', 'name': 'billNumber', 'label': 'billNumber'}, 
    {'type': 'text', 'name': 'codeVolume', 'label': 'codeVolume'}, 
    {'type': 'text', 'name': 'codePages', 'label': 'codePages'}, 
    {'type': 'text', 'name': 'dateDecided', 'label': 'dateDecided'}, 
    {'type': 'text', 'name': 'reporterVolume', 'label': 'reporterVolume'}, 
    {'type': 'text', 'name': 'firstPage', 'label': 'firstPage'}, 
    {'type': 'text', 'name': 'documentNumber', 'label': 'documentNumber'}, 
    {'type': 'text', 'name': 'dateEnacted', 'label': 'dateEnacted'}, 
    {'type': 'text', 'name': 'publicLawNumber', 'label': 'publicLawNumber'}, 
    {'type': 'text', 'name': 'country', 'label': 'country'}, 
    {'type': 'text', 'name': 'applicationNumber', 'label': 'applicationNumber'}, 
    {'type': 'text', 'name': 'forumTitle', 'label': 'forumTitle'}, 
    {'type': 'text', 'name': 'episodeNumber', 'label': 'episodeNumber'}, 
    {'type': 'text', 'name': 'blogTitle', 'label': 'blogTitle'}, 
    {'type': 'text', 'name': 'type', 'label': 'type'}, 
    {'type': 'text', 'name': 'medium', 'label': 'medium'}, 
    {'type': 'text', 'name': 'caseName', 'label': 'caseName'}, 
    {'type': 'text', 'name': 'nameOfAct', 'label': 'nameOfAct'}, 
    {'type': 'text', 'name': 'subject', 'label': 'subject'}, 
    {'type': 'text', 'name': 'proceedingsTitle', 'label': 'proceedingsTitle'}, 
    {'type': 'text', 'name': 'bookTitle', 'label': 'bookTitle'}, 
    {'type': 'text', 'name': 'shortTitle', 'label': 'shortTitle'}, 
    {'type': 'text', 'name': 'docketNumber', 'label': 'docketNumber'}, 
    {'type': 'text', 'name': 'numPages', 'label': 'numPages'}, 
    {'type': 'text', 'name': 'programTitle', 'label': 'programTitle'}, 
    {'type': 'text', 'name': 'issuingAuthority', 'label': 'issuingAuthority'}, 
    {'type': 'text', 'name': 'filingDate', 'label': 'filingDate'}, 
    {'type': 'text', 'name': 'genre', 'label': 'genre'}, 
    {'type': 'text', 'name': 'archive', 'label': 'archive'}
    ]
zotero_fields_mapping_name = dict((f['name'], f) for f in zotero_fields_mapping)
zotero_fields_mapping_id = {}

def like(text):
    sqlite_version = tuple([int(x) for x in ['3','1','2']])
    if sqlite_version >= (3, 1, 0):
        return "LIKE \'%s\' ESCAPE '/'" % text
    else:
        return 'LIKE %s' % text
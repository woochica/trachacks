"""
The MIT License

Copyright (c) 2009 James Cooper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
import httplib
import oauth
from xml.dom import minidom

API_SERVER        = 'https://www.gliffy.com'
API_ROOT          = '/api/1.0'

class GliffyApi:

    def __init__(self, consumer_key, consumer_secret, account_id, username):
        self.consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
        self.signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.oauth_token = None
        self.account_id = account_id
        self.username = username

    def makeGetRequest(self, url, token, parameters):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token, http_method='GET',\
                                                                   http_url=API_SERVER+url, parameters=parameters)
        oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, token)
        outurl = oauth_request.to_url()
        return outurl      

    def makeRequest(self, url, token, parameters):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token, http_method='POST',\
                                                                   http_url=API_SERVER+url, parameters=parameters)
        headers = { 'Accept' : 'text/xml', 'Content-Type' : 'application/x-www-form-urlencoded' }
        oauth_request.sign_request(self.signature_method_hmac_sha1, self.consumer, token)
        connection = httplib.HTTPSConnection('www.gliffy.com')
        #connection.set_debuglevel(5)
        connection.request('POST', url, body=oauth_request.to_postdata(), headers=headers)
        return connection.getresponse()

    def login(self):
        parameters = { 'action' : 'create', 'description' : 'GLIFFY-python-client' }
        url  = "%s/accounts/%s/users/%s/oauth_token.xml" % (API_ROOT, self.account_id, self.username)
        response = self.makeRequest(url, None, parameters)
        respstr = response.read()
        dom = minidom.parseString(respstr)
        token  = dom.getElementsByTagName("oauth-token")[0].childNodes[0].nodeValue
        secret = dom.getElementsByTagName("oauth-token-secret")[0].childNodes[0].nodeValue
        #print "token=%s" % token
        #print "secret=%s" % secret
        self.oauth_token = oauth.OAuthToken(token, secret)

    def findDocIdByName(self, docName):
        parameters = { 'action' : 'get' }
        url = "%s/accounts/%s/documents.xml" % (API_ROOT, self.account_id)
        response = self.makeRequest(url, self.oauth_token, parameters)
        dom = minidom.parseString(response.read())
        names = dom.getElementsByTagName("name")
        for name in names:
            namestr = name.childNodes[0].nodeValue
            if (namestr == docName):
                return name.parentNode.attributes['id'].value
        return None

    def createDoc(self, docName, folderPath):
        parameters = { 'action' : 'create', 'documentName' : docName, 'documentType' : 'diagram' }
        if folderPath:
            parameters['folderPath'] = folderPath
        url = "%s/accounts/%s/documents.xml" % (API_ROOT, self.account_id)
        response = self.makeRequest(url, self.oauth_token, parameters)
        dom = minidom.parseString(response.read())
        documents = dom.getElementsByTagName("document")
        return documents[0].attributes['id'].value

    def getOrCreateDocument(self, docName, folderPath=None):
        docId = self.findDocIdByName(docName)
        if not docId:
            docId = self.createDoc(docName, folderPath)
        return docId

    def getImageUrl(self, docId, extension, size):
        url = "%s/accounts/%s/documents/%s.%s" % (API_ROOT, self.account_id, docId, extension)
        parameters = { 'action' : 'get', 'size' : size }
        return self.makeGetRequest(url, self.oauth_token, parameters)

    def getLaunchDiagramUrl(self, docName, returnUrl):
        docId = self.findDocIdByName(docName)
        parameters = { 'launchDiagramId' : docId, 'returnURL' : returnUrl, 'returnButtonText' : 'Back to trac' }
        return self.makeGetRequest("/gliffy/", self.oauth_token, parameters)

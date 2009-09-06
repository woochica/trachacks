import os
import pysvn
import tempfile
import uuid
import tarfile
import commands


def checkoutsvn(checkoutstr,username,password):

    client = pysvn.Client()
    client.exception_style = 0

    def ssl_server_trust_prompt( trust_dict ):
        return True,0,True

    client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
    
    def get_login( realm, username, may_save ):
        return True, username, password, False

    client.callback_get_login = get_login
    
    try:
        client.checkout(checkoutstr,"./mypkg")
    except pysvn.ClientError, e:
        return False
        
    return True

def generate_tarball(excludelist=[".svn"]):
    #now make tar file

    os.chdir("mypkg")

    excludestr=""
    for iex in excludelist:
        excludestr+=" --exclude %s" % iex

    strcmd="tar czf ../mypkg.tgz * %s"%excludestr

    (status,output)=commands.getstatusoutput(strcmd)

    os.chdir("..")

    if status!=0:
        return False
    else:
        return True

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor

class SVNTarBallPlugin(Component):
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'SVNTarBall'
    def get_navigation_items(self, req):
        yield ('mainnav', 'SVNTarBall',
            html.A('SVNTarBall', href= req.href.SVNTarBall()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/SVNTarBall'
    
    def process_request(self, req):

        success=True

        #check input first
        source=None
        username="guest"
        password=""
        excludelist=[".svn"]

        if req.args.has_key("source"):
            source=req.args["source"]

        if req.args.has_key("username"):
            username=req.args["username"]

        if req.args.has_key("password"):
            password=req.args["password"]
            
        if req.args.has_key("exclude"):
            self.env.log.info("exclude=%s"%req.args["exclude"])
            excludelist=req.args["exclude"].split(" ")

        if not source:
            success=False

        if success:
            #get a tmp dir
            tmpdir="%s/%s"%(tempfile.gettempdir(),str(uuid.uuid4()))

            #get the current dir
            olddir=os.getcwd()
    
            #Not checking name, since uuid won't (frequently :-) be duplicate
            os.mkdir(tmpdir)
    
            #go into the tmp dir and do everything there
            os.chdir(tmpdir)
    
            #checkout the package from svn
            success=checkoutsvn(source,username,password)

            if success:
                #make the tar
                success=generate_tarball(excludelist)
    
            #go back to where it was
            os.chdir(olddir)
    
        if success:
            #serve the tar file
            req.send_response(200)
            req.send_header('Content-Type', 'application/x-gtar')
            req.end_headers()

            f = open(tmpdir+"/mypkg.tgz", 'rb')

            while True:
                data = f.read(1024 * 8) # Read blocks of 8KB at a time
                if not data: break
                req.write(data)

            #then remove the tmp folder here
                

        else:
            #return 404 error
            req.send_response(404)
            req.send_header('Content-Type', 'application/text-html')
            req.end_headers()
        
